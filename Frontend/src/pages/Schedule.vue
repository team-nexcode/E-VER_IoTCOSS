<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { Plus, Check, Trash2 } from 'lucide-vue-next'
import { useDeviceStore } from '@/stores/device'
import { storeToRefs } from 'pinia'

type ScheduleAction = 'on' | 'off'
interface DeviceSchedule {
  id: string
  deviceId: number
  time: string // "HH:MM"
  action: ScheduleAction
}

const LS_SCHEDULES = 'aiot_schedules'

/** ===== Store ===== */
const store = useDeviceStore()
const { devices } = storeToRefs(store)

/** ===== 서버 동기화 시간(대시보드 좌측하단 기준과 동일) ===== */
const serverOffset = ref<number | null>(null)

async function syncTimeOnce() {
  try {
    const res = await fetch('/api/health')
    if (!res.ok) throw new Error('health not ok')
    const data = await res.json()
    const serverMs = new Date(data.server_time).getTime()
    serverOffset.value = serverMs - Date.now()
  } catch {
    serverOffset.value = null
  }
}
function getNow(): Date {
  return serverOffset.value === null ? new Date() : new Date(Date.now() + serverOffset.value)
}
function pad2(n: number) {
  return String(n).padStart(2, '0')
}

/** ===== Schedules list (저장/표시) ===== */
function safeParse<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback
  try {
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

const schedules = ref<DeviceSchedule[]>([])

function loadSchedules() {
  const list = safeParse<any[]>(localStorage.getItem(LS_SCHEDULES), [])
  schedules.value = Array.isArray(list)
    ? list
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
    : []
}

function saveSchedules() {
  localStorage.setItem(LS_SCHEDULES, JSON.stringify(schedules.value))
}

function makeId() {
  return `${Date.now()}_${Math.random().toString(16).slice(2)}`
}

function getDeviceName(id: number) {
  return devices.value.find((d) => d.id === id)?.name ?? `Device #${id}`
}
function getDeviceLoc(id: number) {
  return devices.value.find((d) => d.id === id)?.location ?? ''
}

function removeSchedule(id: string) {
  schedules.value = schedules.value.filter((s) => s.id !== id)
  saveSchedules()
}

/** ===== Modal State ===== */
const isOpen = ref(false)
const selectedDeviceId = ref<number | null>(null)
const action = ref<ScheduleAction>('on')
const hour = ref(0)
const minute = ref(0)

/** ===== Wheel Picker (하이라이트/선택 정확히 일치) ===== */
const ITEM_H = 44
const WHEEL_H = 240
const PAD = Math.round((WHEEL_H - ITEM_H) / 2) // ✅ 중앙 정확히

const H_REPEAT = 7
const M_REPEAT = 5

const hourWheel = ref<HTMLDivElement | null>(null)
const minWheel = ref<HTMLDivElement | null>(null)

const hoursList = computed(() => {
  const base = Array.from({ length: 24 }, (_, i) => i)
  return Array.from({ length: 24 * H_REPEAT }, (_, i) => base[i % 24])
})
const minutesList = computed(() => {
  const base = Array.from({ length: 60 }, (_, i) => i)
  return Array.from({ length: 60 * M_REPEAT }, (_, i) => base[i % 60])
})

const hIndex = ref(0)
const mIndex = ref(0)

let rafH = 0
let rafM = 0
let hSnapTimer: number | null = null
let mSnapTimer: number | null = null

function normalizeInfinite(el: HTMLDivElement, cycleCount: number, repeat: number) {
  const cyclePx = cycleCount * ITEM_H
  const minPx = cyclePx
  const maxPx = cyclePx * (repeat - 2)

  if (el.scrollTop < minPx) el.scrollTop += cyclePx * (repeat - 3)
  if (el.scrollTop > maxPx) el.scrollTop -= cyclePx * (repeat - 3)
}

function settle(el: HTMLDivElement, idx: number) {
  el.scrollTo({ top: idx * ITEM_H, behavior: 'smooth' })
}

function setWheelTo(h: number, m: number) {
  const hm = Math.floor(H_REPEAT / 2) * 24 + h
  const mm = Math.floor(M_REPEAT / 2) * 60 + m
  hIndex.value = hm
  mIndex.value = mm
  if (hourWheel.value) hourWheel.value.scrollTop = hm * ITEM_H
  if (minWheel.value) minWheel.value.scrollTop = mm * ITEM_H
}

function onHourScroll() {
  if (!hourWheel.value) return
  if (rafH) cancelAnimationFrame(rafH)

  rafH = requestAnimationFrame(() => {
    const el = hourWheel.value!
    normalizeInfinite(el, 24, H_REPEAT)
    const idx = Math.round(el.scrollTop / ITEM_H)

    hIndex.value = idx
    hour.value = hoursList.value[idx] ?? 0

    if (hSnapTimer) window.clearTimeout(hSnapTimer)
    hSnapTimer = window.setTimeout(() => settle(el, idx), 110)
  })
}

function onMinScroll() {
  if (!minWheel.value) return
  if (rafM) cancelAnimationFrame(rafM)

  rafM = requestAnimationFrame(() => {
    const el = minWheel.value!
    normalizeInfinite(el, 60, M_REPEAT)
    const idx = Math.round(el.scrollTop / ITEM_H)

    mIndex.value = idx
    minute.value = minutesList.value[idx] ?? 0

    if (mSnapTimer) window.clearTimeout(mSnapTimer)
    mSnapTimer = window.setTimeout(() => settle(el, idx), 110)
  })
}

function wheelClickHour(i: number) {
  hourWheel.value?.scrollTo({ top: i * ITEM_H, behavior: 'smooth' })
}
function wheelClickMin(i: number) {
  minWheel.value?.scrollTo({ top: i * ITEM_H, behavior: 'smooth' })
}

/** ===== Open/Close ===== */
async function openModal() {
  isOpen.value = true
  selectedDeviceId.value = devices.value[0]?.id ?? null
  action.value = 'on'

  // ✅ 기본 시간 = 현재 시간(서버 기준)
  await syncTimeOnce()
  const now = getNow()
  hour.value = now.getHours()
  minute.value = now.getMinutes()

  nextTick(() => setWheelTo(hour.value, minute.value))
}

function closeModal() {
  isOpen.value = false
}

function confirmModal() {
  if (selectedDeviceId.value === null) return

  const t = `${pad2(hour.value)}:${pad2(minute.value)}`
  schedules.value.push({
    id: makeId(),
    deviceId: selectedDeviceId.value,
    time: t,
    action: action.value,
  })
  saveSchedules()
  closeModal()
}

const selectedTimeText = computed(() => `${pad2(hour.value)}:${pad2(minute.value)}`)

onMounted(() => {
  loadSchedules()
})
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-white">스케줄</h2>
    </div>

    <!-- iOS-ish grouped list -->
    <div class="rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden">
      <!-- 알람 목록 -->
      <div v-if="schedules.length" class="divide-y divide-white/10">
        <div
          v-for="s in schedules"
          :key="s.id"
          class="px-4 py-3 flex items-center justify-between gap-4 hover:bg-white/[0.04] transition"
        >
          <div class="min-w-0">
            <div class="flex items-center gap-3">
              <div class="text-[22px] font-mono font-bold text-white tracking-wider">
                {{ s.time }}
              </div>

              <span
                class="text-[11px] font-bold px-2 py-1 rounded-full border"
                :class="s.action === 'on'
                  ? 'bg-green-500/15 text-green-200 border-green-500/25'
                  : 'bg-red-500/15 text-red-200 border-red-500/25'"
              >
                {{ s.action.toUpperCase() }}
              </span>
            </div>

            <div class="text-sm text-white/70 truncate mt-0.5">
              {{ getDeviceName(s.deviceId) }}
              <span class="text-white/35" v-if="getDeviceLoc(s.deviceId)">· {{ getDeviceLoc(s.deviceId) }}</span>
            </div>
          </div>

          <button
            type="button"
            class="p-2 rounded-xl text-white/35 hover:text-white/75 hover:bg-white/[0.04] transition"
            @click="removeSchedule(s.id)"
            aria-label="delete"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- 알람추가 중앙 정렬 -->
      <button
        type="button"
        class="w-full h-14 border-t border-white/10 hover:bg-white/[0.05] active:bg-white/[0.06] transition
               flex items-center justify-center gap-2"
        :class="schedules.length ? '' : 'border-t-0'"
        @click="openModal"
      >
        <span class="w-7 h-7 grid place-items-center rounded-full bg-white/[0.06] border border-white/10">
          <Plus class="w-4 h-4 text-white/80" />
        </span>
        <span class="text-base font-semibold text-white">알람 추가</span>
      </button>
    </div>

    <!-- Modal -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-md"
      @click.self="closeModal"
    >
      <div class="w-full sm:max-w-xl sm:w-[560px] px-3 sm:px-0 pb-3 sm:pb-0">
        <!-- 모달 외곽 = 직각 -->
        <div class="bg-[#0b1220] ring-1 ring-white/12 overflow-hidden rounded-none">
          <!-- Top bar -->
          <div class="px-6 pt-6 pb-4 flex items-center justify-between border-b border-white/10">
            <button
              type="button"
              class="text-sky-300 hover:text-sky-200 transition text-[17px] font-semibold"
              @click="closeModal"
            >
              취소
            </button>

            <div class="text-white text-[20px] font-bold">알람</div>

            <button
              type="button"
              class="text-sky-300 hover:text-sky-200 transition text-[17px] font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="selectedDeviceId === null"
              @click="confirmModal"
            >
              완료
            </button>
          </div>

          <div class="px-5 py-5 space-y-4">
            <!-- 디바이스 선택만 직각 -->
            <div class="bg-white/[0.04] ring-1 ring-white/10 overflow-hidden rounded-none">
              <div class="divide-y divide-white/10">
                <button
                  v-for="d in devices"
                  :key="d.id"
                  type="button"
                  class="w-full px-4 py-3 flex items-center justify-between gap-3 hover:bg-white/[0.05] transition text-left"
                  @click="selectedDeviceId = d.id"
                >
                  <div class="min-w-0">
                    <p class="text-[16px] font-semibold text-white truncate">{{ d.name }}</p>
                    <p class="text-[12px] text-white/45 truncate mt-0.5">{{ d.location }}</p>
                  </div>
                  <Check v-if="selectedDeviceId === d.id" class="w-6 h-6 text-sky-300 flex-shrink-0" />
                </button>

                <div v-if="devices.length === 0" class="px-4 py-5 text-sm text-white/45">
                  디바이스 없음
                </div>
              </div>
            </div>

            <!-- 시간 설정(라운드 유지) -->
            <div class="bg-white/[0.04] ring-1 ring-white/10 overflow-hidden rounded-2xl">
              <div class="relative px-4 py-5">
                <div class="flex items-center justify-center gap-6">
                  <!-- Hour -->
                  <div class="relative">
                    <div
                      ref="hourWheel"
                      class="wheel w-[92px]"
                      :style="{
                        height: WHEEL_H + 'px',
                        paddingTop: PAD + 'px',
                        paddingBottom: PAD + 'px',
                        scrollPaddingTop: PAD + 'px',
                        scrollPaddingBottom: PAD + 'px',
                      }"
                      @scroll="onHourScroll"
                    >
                      <div
                        v-for="(v, i) in hoursList"
                        :key="`h_${i}`"
                        class="h-[44px] flex items-center justify-center snap-center"
                      >
                        <button type="button" class="w-full h-full grid place-items-center" @click="wheelClickHour(i)">
                          <span
                            :class="[
                              'font-mono text-[28px] transition',
                              i === hIndex ? 'text-white' : 'text-white/35',
                            ]"
                          >
                            {{ pad2(v) }}
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>

                  <div class="text-4xl font-mono text-white/35 -mt-1">:</div>

                  <!-- Minute -->
                  <div class="relative">
                    <div
                      ref="minWheel"
                      class="wheel w-[92px]"
                      :style="{
                        height: WHEEL_H + 'px',
                        paddingTop: PAD + 'px',
                        paddingBottom: PAD + 'px',
                        scrollPaddingTop: PAD + 'px',
                        scrollPaddingBottom: PAD + 'px',
                      }"
                      @scroll="onMinScroll"
                    >
                      <div
                        v-for="(v, i) in minutesList"
                        :key="`m_${i}`"
                        class="h-[44px] flex items-center justify-center snap-center"
                      >
                        <button type="button" class="w-full h-full grid place-items-center" @click="wheelClickMin(i)">
                          <span
                            :class="[
                              'font-mono text-[28px] transition',
                              i === mIndex ? 'text-white' : 'text-white/35',
                            ]"
                          >
                            {{ pad2(v) }}
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 하이라이트 위치 정확히: top = PAD -->
                <div class="pointer-events-none absolute left-0 right-0 px-4" :style="{ top: PAD + 'px' }">
                  <div class="h-[44px] rounded-xl bg-white/[0.06] border border-white/10" />
                </div>

                <div class="mt-4 text-center text-[20px] font-mono font-bold text-white tracking-wider">
                  {{ selectedTimeText }}
                </div>
              </div>
            </div>

            <!-- ON/OFF(라운드 유지) + 색상(초록/빨강) -->
            <div class="bg-white/[0.04] ring-1 ring-white/10 overflow-hidden rounded-2xl">
              <div class="grid grid-cols-2">
                <button
                  type="button"
                  class="h-12 text-[15px] font-bold transition border-r border-white/10"
                  :class="action === 'on'
                    ? 'bg-green-600 text-white'
                    : 'bg-transparent text-white/70 hover:bg-white/[0.04]'"
                  @click="action = 'on'"
                >
                  ON
                </button>
                <button
                  type="button"
                  class="h-12 text-[15px] font-bold transition"
                  :class="action === 'off'
                    ? 'bg-red-600 text-white'
                    : 'bg-transparent text-white/70 hover:bg-white/[0.04]'"
                  @click="action = 'off'"
                >
                  OFF
                </button>
              </div>
            </div>

            <div class="h-1" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wheel {
  overflow-y: auto;
  scroll-snap-type: y mandatory;
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.wheel::-webkit-scrollbar {
  display: none;
}
</style>
