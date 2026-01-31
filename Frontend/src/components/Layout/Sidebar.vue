<script setup lang="ts">
import { ref, onMounted, onUnmounted, type Component } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import {
  LayoutDashboard,
  Plug,
  BarChart3,
  Clock,
  Bell,
  FileText,
  Settings,
} from 'lucide-vue-next'

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
  { to: '/api-logs', icon: FileText, label: 'API 로그' },
  { to: '/settings', icon: Settings, label: '설정' },
]

const route = useRoute()

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
}

function isActive(to: string): boolean {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
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
</script>

<template>
  <aside class="fixed left-0 top-[60px] bottom-0 w-[230px] bg-[#111827] border-r border-gray-800 flex flex-col z-40">
    <nav class="flex-1 py-6 px-5 space-y-4 overflow-y-auto">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="[
          'flex items-center gap-5 px-6 py-5 rounded-3xl text-lg font-bold transition-all duration-200',
          isActive(item.to)
            ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
            : 'text-gray-300 hover:text-white hover:bg-gray-800/70',
        ]"
      >
        <component :is="item.icon" class="w-6 h-6 flex-shrink-0" />
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>

    <!-- 하단 -->
    <div class="p-4 border-t border-gray-800 space-y-3">
      <!-- 서버 동기화 시계 -->
      <div class="bg-gray-800/50 rounded-xl p-3 text-center">
        <template v-if="status === 'offline'">
          <p class="text-sm font-mono font-bold text-red-400">통신 오류</p>
          <p class="text-[10px] text-red-500/70 mt-1">서버 연결 실패</p>
        </template>
        <template v-else-if="serverOffset !== null">
          <p class="text-lg font-mono font-bold text-white tracking-wider">{{ displayTime }}</p>
          <p class="text-[10px] text-gray-500 mt-0.5">{{ displayDate }}</p>
        </template>
        <template v-else>
          <p class="text-sm font-mono text-yellow-400">동기화 중...</p>
        </template>
      </div>

      <!-- 시스템 상태 -->
      <div class="bg-gray-800/50 rounded-xl p-3">
        <div class="flex items-center gap-2 mb-2">
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
        <p class="text-[10px] text-gray-600 mt-1">
          서버 응답: {{ status === 'online' && responseTime !== null ? `${responseTime}ms` : status === 'offline' ? '—' : '측정 중...' }}
        </p>
      </div>
    </div>
  </aside>
</template>
