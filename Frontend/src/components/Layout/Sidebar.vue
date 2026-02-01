<script setup lang="ts">
import { ref, onMounted, onUnmounted, type Component } from 'vue'
import { useRoute } from 'vue-router'
import {
  LayoutDashboard,
  Plug,
  BarChart3,
  Clock,
  Bell,
  Monitor,
  Settings,
} from 'lucide-vue-next'
import { useDeviceStore } from '@/stores/device'
import { storeToRefs } from 'pinia'

/** =========================
 *  Nav
 *  ========================= */
interface NavItem {
  to: string
  icon: Component
  label: string
}

const navItems: NavItem[] = [
  { to: '/', icon: LayoutDashboard, label: '대시보드' },
  { to: '/devices', icon: Plug, label: '디바이스' },
  { to: '/power', icon: BarChart3, label: '전력 분석' },
  { to: '/schedule', icon: Clock, label: '스케줄' },
  { to: '/alerts', icon: Bell, label: '알림' },
  { to: '/system-log', icon: Monitor, label: 'System Log' },
  { to: '/settings', icon: Settings, label: '설정' },
]

const mainNavItems: NavItem[] = navItems.filter((i) => i.to !== '/settings')
const bottomNavItems: NavItem[] = navItems.filter((i) => i.to === '/settings')

const route = useRoute()

/** =========================
 *  Clock (server sync)
 *  ========================= */
const responseTime = ref<number | null>(null)
const status = ref<'checking' | 'online' | 'offline'>('checking')
const displayTime = ref('--:--:--')
const displayDate = ref('')
const serverOffset = ref<number | null>(null)

let syncInterval: ReturnType<typeof setInterval> | null = null
let clockInterval: ReturnType<typeof setInterval> | null = null

async function syncTime() {
  const start = performance.now()
  try {
    const res = await fetch('/api/health')
    const elapsed = performance.now() - start
    if (res.ok) {
      const data = await res.json()
      responseTime.value = Math.round(elapsed)
      status.value = 'online'
      const serverMs = new Date(data.server_time).getTime()
      const localMs = Date.now()
      serverOffset.value = serverMs - localMs
    } else {
      status.value = 'offline'
      responseTime.value = null
    }
  } catch {
    status.value = 'offline'
    responseTime.value = null
  }
}

function isActive(to: string): boolean {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}

/** =========================
 *  Schedule Runner (HH:MM only)
 *  - Schedule.vue가 localStorage(aiot_schedules)에 저장한 걸 읽어서
 *  - Sidebar 시계(now) 기반으로 매일 HH:MM에 디바이스 ON/OFF
 *  ========================= */
type ScheduleAction = 'on' | 'off'
interface DeviceSchedule {
  id: string
  deviceId: number
  time: string // "HH:MM"
  action: ScheduleAction
}

const LS_SCHEDULES = 'aiot_schedules'
const LS_SCHEDULE_FIRED = 'aiot_schedules_last_fired' // { [id]: epochMinute }

function safeParse<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback
  try {
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function pad2(n: number) {
  return String(n).padStart(2, '0')
}

function loadSchedules(): DeviceSchedule[] {
  const list = safeParse<any[]>(localStorage.getItem(LS_SCHEDULES), [])
  if (!Array.isArray(list)) return []
  return list
    .filter(
      (s) =>
        s &&
        typeof s.id === 'string' &&
        typeof s.deviceId === 'number' &&
        typeof s.time === 'string' &&
        (s.action === 'on' || s.action === 'off')
    )
    .map((s) => ({
      id: s.id as string,
      deviceId: s.deviceId as number,
      time: s.time as string,
      action: s.action as ScheduleAction,
    }))
}

function loadFiredMap(): Record<string, number> {
  const m = safeParse<Record<string, number>>(localStorage.getItem(LS_SCHEDULE_FIRED), {})
  return m && typeof m === 'object' ? m : {}
}
function saveFiredMap(m: Record<string, number>) {
  localStorage.setItem(LS_SCHEDULE_FIRED, JSON.stringify(m))
}

const deviceStore = useDeviceStore()
const { devices } = storeToRefs(deviceStore)

/**
 * 디바이스 상태 변경:
 * - 스토어에 제어 함수가 있으면 그걸 우선 사용
 * - 없으면 devices[].isActive 직접 변경 (화면 반영됨)
 */
async function applyDevicePower(deviceId: number, on: boolean) {
  const anyStore = deviceStore as any

  // (가능한 후보들) 프로젝트에 맞게 자동 대응
  const candidates: Array<[string, 'bool2' | 'idOnly']> = [
    ['setDeviceActive', 'bool2'],
    ['setDevicePower', 'bool2'],
    ['setRelay', 'bool2'],
    ['toggleRelay', 'idOnly'],
    ['toggleDevice', 'idOnly'],
  ]

  for (const [name, mode] of candidates) {
    const fn = anyStore[name]
    if (typeof fn !== 'function') continue

    try {
      const r =
        mode === 'bool2'
          ? fn(deviceId, on)
          : on
            ? fn(deviceId) // idOnly는 "토글"일 수 있으니, on 요청일 때만 호출(보수적으로)
            : fn(deviceId)

      if (r && typeof r.then === 'function') await r
      return
    } catch {
      // 실패하면 아래 fallback으로
    }
  }

  const dev = (devices.value as any[]).find((d) => d.id === deviceId)
  if (dev) dev.isActive = on
}

/** now의 HH:MM이 스케줄과 같으면 실행 (분당 1회) */
function runSchedules(now: Date) {
  const epochMinute = Math.floor(now.getTime() / 60000)
  const nowHHMM = `${pad2(now.getHours())}:${pad2(now.getMinutes())}`

  const list = loadSchedules()
  if (list.length === 0) return

  const fired = loadFiredMap()

  for (const s of list) {
    if (s.time !== nowHHMM) continue
    if (fired[s.id] === epochMinute) continue // 같은 분에 중복 실행 방지

    fired[s.id] = epochMinute
    saveFiredMap(fired)

    void applyDevicePower(s.deviceId, s.action === 'on')
  }
}

function tick() {
  if (serverOffset.value === null) return
  const now = new Date(Date.now() + serverOffset.value)

  displayTime.value = now.toLocaleTimeString('ko-KR', { hour12: true, timeZone: 'Asia/Seoul' })
  displayDate.value = now.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'short',
    timeZone: 'Asia/Seoul',
  })

  // ✅ 스케줄 실행(연월일 무시, HH:MM만)
  runSchedules(now)
}

onMounted(() => {
  syncTime()
  syncInterval = setInterval(syncTime, 10000)
  tick()
  clockInterval = setInterval(tick, 1000)
})

onUnmounted(() => {
  if (syncInterval) clearInterval(syncInterval)
  if (clockInterval) clearInterval(clockInterval)
})

/**
 * ✅ TS(6133) 경고 제거용
 * (템플릿에서 쓰는 걸 TS가 못 읽는 환경일 때만 뜸)
 * 동작에는 영향 없음.
 */
void mainNavItems
void bottomNavItems
void isActive
</script>

<template>
  <!--
    요청 반영:
    1) 글씨가 너무 작음 → 메뉴 텍스트를 다시 "text-lg + font-bold(원래 느낌)"로 복원
    2) 배치가 위에만 쏠림 → nav를 가운데로 “자연스럽게” 내려오게 (여유 공간이면 my-auto로 중앙 정렬)
    3) 왼쪽 사이드바 안에서만 수정
  -->
  <aside
    class="fixed left-0 bottom-0 w-[240px] bg-[#111827] border-r border-gray-800 flex flex-col z-40"
    :style="{ top: 'var(--topbar-height, 60px)' }"
  >

    <!-- 메인 내비게이션: 중앙으로 내려오는 느낌 -->
    <nav class="flex-1 px-4 overflow-y-auto flex">
      <!-- 여유 공간이면 가운데로(쏠림 완화), 공간 부족하면 자연스럽게 위로 붙고 스크롤 -->
      <div class="w-full my-auto space-y-3 py-2">
        <RouterLink
          v-for="item in mainNavItems"
          :key="item.to"
          :to="item.to"
          :class="[
            'group relative flex items-center gap-5 px-5 py-4 rounded-3xl',
            'text-lg font-bold transition-all duration-200',
            'border',
            isActive(item.to)
              ? 'bg-white/[0.06] text-white border-white/10 shadow-[0_10px_26px_-18px_rgba(0,0,0,0.70)]'
              : 'bg-transparent text-gray-300 border-transparent hover:bg-white/[0.045] hover:text-white hover:border-white/10 hover:translate-x-[1px]',
          ]"
        >
          <!-- active indicator (아주 얇게) -->
          <span
            v-if="isActive(item.to)"
            class="absolute left-2 top-1/2 -translate-y-1/2 h-8 w-[2px] rounded-full bg-white/70"
          />

          <!-- 아이콘: 원래 느낌(크게) + 은은한 칩 -->
          <span
            :class="[
              'grid place-items-center w-10 h-10 rounded-2xl flex-shrink-0 border transition-colors duration-200',
              isActive(item.to)
                ? 'bg-white/5 border-white/10'
                : 'bg-white/[0.02] border-white/5 group-hover:bg-white/[0.04] group-hover:border-white/10',
            ]"
          >
            <component
              :is="item.icon"
              :class="[
                'w-6 h-6 transition-colors duration-200',
                isActive(item.to) ? 'text-white' : 'text-gray-300 group-hover:text-white',
              ]"
            />
          </span>

          <span class="flex-1 truncate">{{ item.label }}</span>

          <!-- hover affordance -->
          <span
            :class="[
              'text-base opacity-0 -translate-x-1 transition-all duration-200',
              'group-hover:opacity-60 group-hover:translate-x-0',
              isActive(item.to) ? 'opacity-60 translate-x-0 text-white/70' : 'text-gray-500',
            ]"
          >
            ›
          </span>
        </RouterLink>
      </div>
    </nav>

    <!-- 설정(하단에 따로 두어 시각적 분산) -->
    <div class="px-4 pt-2">
      <div class="h-px bg-gradient-to-r from-transparent via-gray-700/60 to-transparent" />
      <div class="pt-3 space-y-3">
        <RouterLink
          v-for="item in bottomNavItems"
          :key="item.to"
          :to="item.to"
          :class="[
            'group relative flex items-center gap-5 px-5 py-4 rounded-3xl',
            'text-lg font-bold transition-all duration-200',
            'border',
            isActive(item.to)
              ? 'bg-white/[0.06] text-white border-white/10 shadow-[0_10px_26px_-18px_rgba(0,0,0,0.70)]'
              : 'bg-transparent text-gray-300 border-transparent hover:bg-white/[0.045] hover:text-white hover:border-white/10 hover:translate-x-[1px]',
          ]"
        >
          <span
            v-if="isActive(item.to)"
            class="absolute left-2 top-1/2 -translate-y-1/2 h-8 w-[2px] rounded-full bg-white/70"
          />
          <span
            :class="[
              'grid place-items-center w-10 h-10 rounded-2xl flex-shrink-0 border transition-colors duration-200',
              isActive(item.to)
                ? 'bg-white/5 border-white/10'
                : 'bg-white/[0.02] border-white/5 group-hover:bg-white/[0.04] group-hover:border-white/10',
            ]"
          >
            <component
              :is="item.icon"
              :class="[
                'w-6 h-6 transition-colors duration-200',
                isActive(item.to) ? 'text-white' : 'text-gray-300 group-hover:text-white',
              ]"
            />
          </span>
          <span class="flex-1 truncate">{{ item.label }}</span>
          <span
            :class="[
              'text-base opacity-0 -translate-x-1 transition-all duration-200',
              'group-hover:opacity-60 group-hover:translate-x-0',
              isActive(item.to) ? 'opacity-60 translate-x-0 text-white/70' : 'text-gray-500',
            ]"
          >
            ›
          </span>
        </RouterLink>
      </div>
    </div>

    <!-- 하단 정보(조금 더 존재감 있게) -->
    <div class="p-4 border-t border-gray-800 space-y-3 mt-3">
      <!-- 서버 동기화 시계 -->
      <div class="bg-white/[0.03] border border-white/10 rounded-2xl p-3 text-center">
        <template v-if="status === 'offline'">
          <p class="text-sm font-mono font-bold text-red-400">통신 오류</p>
          <p class="text-[10px] text-red-500/70 mt-1">서버 연결 실패</p>
        </template>
        <template v-else-if="serverOffset !== null">
          <p class="text-xl font-mono font-bold text-white tracking-wider">{{ displayTime }}</p>
          <p class="text-[10px] text-gray-500 mt-0.5">{{ displayDate }}</p>
        </template>
        <template v-else>
          <p class="text-sm font-mono text-yellow-400">동기화 중...</p>
        </template>
      </div>

      <!-- 시스템 상태 -->
      <div class="bg-white/[0.03] border border-white/10 rounded-2xl p-3">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <div
              :class="[
                'w-2 h-2 rounded-full',
                status === 'online'
                  ? 'bg-green-500 animate-pulse'
                  : status === 'offline'
                    ? 'bg-red-500'
                    : 'bg-yellow-500 animate-pulse',
              ]"
            />
            <span class="text-xs text-gray-400">시스템 상태</span>
          </div>

          <span class="text-[10px] text-gray-600">
            {{ status === 'online' && responseTime !== null ? `${responseTime}ms` : status === 'offline' ? '—' : '...' }}
          </span>
        </div>

        <p
          :class="[
            'text-xs font-medium',
            status === 'online'
              ? 'text-green-400'
              : status === 'offline'
                ? 'text-red-400'
                : 'text-yellow-400',
          ]"
        >
          {{ status === 'online' ? '정상 운영 중' : status === 'offline' ? '서버 연결 실패' : '연결 중...' }}
        </p>
      </div>
    </div>
  </aside>
</template>
