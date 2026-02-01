<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { Plus, Check } from 'lucide-vue-next'
import { useDeviceStore } from '@/stores/device'
import { useScheduleStore } from '@/stores/schedule'
import { storeToRefs } from 'pinia'

type ScheduleAction = 'on' | 'off'

/** ===== Store ===== */
const store = useDeviceStore()
const { devices } = storeToRefs(store)

const scheduleStore = useScheduleStore()

onMounted(() => {
  scheduleStore.fetchSchedules()
})

/** ===== 서버 동기화 시간 (대시보드 좌측하단 기준과 동일) ===== */
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

/** ===== Modal State ===== */
const isOpen = ref(false)
const selectedDeviceId = ref<number | null>(null)
const action = ref<ScheduleAction>('on')
const hour = ref(0)
const minute = ref(0)

/** ===== Wheel Picker ===== */
const ITEM_H = 44
const PAD = ITEM_H * 2
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
    hSnapTimer = window.setTimeout(() => settle(el, idx), 120)
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
    mSnapTimer = window.setTimeout(() => settle(el, idx), 120)
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

  await syncTimeOnce()
  const now = getNow()
  hour.value = now.getHours()
  minute.value = now.getMinutes()

  nextTick(() => setWheelTo(hour.value, minute.value))
}

function closeModal() {
  isOpen.value = false
}

/** NOTE: 저장/실행 로직은 여기서 안 함(요청대로 UI만) */
async function confirmModal() {
  if (selectedDeviceId.value === null) return
  
  const selectedDevice = devices.value.find(d => d.id === selectedDeviceId.value)
  if (!selectedDevice) return
  
  // ON: 선택 시간에 켜기, OFF: 선택 시간에 끄기
  const selectedTime = `${pad2(hour.value)}:${pad2(minute.value)}:00`
  
  const scheduleName = action.value === 'on'
    ? `${selectedDevice.name} ${pad2(hour.value)}:${pad2(minute.value)} ON`
    : `${selectedDevice.name} ${pad2(hour.value)}:${pad2(minute.value)} OFF`

  const success = await scheduleStore.createSchedule({
    device_mac: selectedDevice.deviceMac,
    schedule_name: scheduleName,
    start_time: action.value === 'on' ? selectedTime : '00:00:00', // ON이면 이 시간에 켜기
    end_time: action.value === 'off' ? selectedTime : '23:59:59',   // OFF면 이 시간에 끄기
    enabled: true,
    days_of_week: '0,1,2,3,4,5,6'
  })
  
  if (success) {
    alert('스케줄이 등록되었습니다.')
  }
  
  closeModal()
}

const selectedTimeText = computed(() => `${pad2(hour.value)}:${pad2(minute.value)}`)
</script>

<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-white">스케줄</h2>

      <button
        type="button"
        class="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-white/[0.06] hover:bg-white/[0.10] border border-white/10 text-white transition"
        @click="openModal"
      >
        <Plus class="w-4 h-4" />
        <span class="text-sm font-semibold">알람 추가</span>
      </button>
    </div>

    <!-- 스케줄 목록 -->
    <div v-if="scheduleStore.schedules.length > 0" class="space-y-3">
      <div
        v-for="schedule in scheduleStore.schedules"
        :key="schedule.id"
        class="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4"
      >
        <div class="flex items-center justify-between">
          <div class="flex-1 min-w-0">
            <h3 class="text-sm font-semibold text-white truncate">{{ schedule.schedule_name }}</h3>
            <p class="text-xs text-gray-400 mt-1">
              {{ schedule.start_time.slice(0, 5) }} ~ {{ schedule.end_time.slice(0, 5) }}
            </p>
            <p class="text-xs text-gray-500 mt-0.5">{{ schedule.device_mac }}</p>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="scheduleStore.toggleSchedule(schedule.id, !schedule.enabled)"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-medium transition',
                schedule.enabled
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                  : 'bg-gray-700/50 text-gray-400 border border-gray-600/30'
              ]"
            >
              {{ schedule.enabled ? '활성' : '비활성' }}
            </button>
            <button
              @click="scheduleStore.deleteSchedule(schedule.id)"
              class="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 transition"
            >
              삭제
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-12 text-gray-500">
      등록된 스케줄이 없습니다.
    </div>

    <!-- Modal -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm"
      @click.self="closeModal"
    >
      <div class="w-full sm:max-w-lg sm:w-[520px] px-3 sm:px-0 pb-3 sm:pb-0">
        <div class="rounded-3xl bg-[#0b1220] border border-white/10 shadow-2xl overflow-hidden">
          <!-- iOS style topbar (corner clipping 방지: 패딩 충분) -->
          <div class="px-6 pt-5 pb-4 flex items-center justify-between">
            <button
              type="button"
              class="px-3 py-2 rounded-2xl bg-white/[0.06] hover:bg-white/[0.10] border border-white/10 text-gray-200 hover:text-white transition"
              @click="closeModal"
            >
              취소
            </button>

            <div class="text-center">
              <p class="text-lg font-semibold text-white leading-none">알람</p>
            </div>

            <button
              type="button"
              class="px-3 py-2 rounded-2xl bg-sky-500/90 hover:bg-sky-500 text-white font-semibold transition disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="selectedDeviceId === null"
              @click="confirmModal"
            >
              완료
            </button>
          </div>

          <div class="px-6 pb-6 space-y-5">
            <!-- Device list -->
            <div class="bg-white/[0.03] border border-white/10 rounded-2xl overflow-hidden">
              <button
                v-for="d in devices"
                :key="d.id"
                type="button"
                class="w-full px-4 py-3 flex items-center justify-between gap-3 hover:bg-white/[0.06] transition text-left"
                @click="selectedDeviceId = d.id"
              >
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-white truncate">{{ d.name }}</p>
                  <p class="text-[11px] text-gray-500 truncate">{{ d.location }}</p>
                </div>
                <Check v-if="selectedDeviceId === d.id" class="w-5 h-5 text-sky-300 flex-shrink-0" />
              </button>

              <div v-if="devices.length === 0" class="px-4 py-5 text-sm text-gray-500">
                디바이스 없음
              </div>
            </div>

            <!-- Time picker -->
            <div class="bg-white/[0.03] border border-white/10 rounded-2xl p-4">
              <div class="flex items-center justify-center gap-4">
                <!-- Hour -->
                <div class="relative">
                  <div
                    ref="hourWheel"
                    class="wheel h-[220px] w-[92px]"
                    :style="{ paddingTop: PAD + 'px', paddingBottom: PAD + 'px' }"
                    @scroll="onHourScroll"
                  >
                    <div
                      v-for="(v, i) in hoursList"
                      :key="`h_${i}`"
                      class="h-[44px] flex items-center justify-center snap-center"
                    >
                      <button type="button" class="w-full h-full flex items-center justify-center" @click="wheelClickHour(i)">
                        <span
                          :class="[
                            'font-mono text-2xl transition',
                            i === hIndex ? 'text-white font-semibold' : 'text-gray-500',
                          ]"
                        >
                          {{ pad2(v) }}
                        </span>
                      </button>
                    </div>
                  </div>

                  <div class="pointer-events-none absolute inset-0 flex items-center justify-center">
                    <div class="h-[44px] w-full rounded-xl bg-white/[0.06] border border-white/10" />
                  </div>
                </div>

                <div class="text-3xl font-mono text-white/60 -mt-1">:</div>

                <!-- Minute -->
                <div class="relative">
                  <div
                    ref="minWheel"
                    class="wheel h-[220px] w-[92px]"
                    :style="{ paddingTop: PAD + 'px', paddingBottom: PAD + 'px' }"
                    @scroll="onMinScroll"
                  >
                    <div
                      v-for="(v, i) in minutesList"
                      :key="`m_${i}`"
                      class="h-[44px] flex items-center justify-center snap-center"
                    >
                      <button type="button" class="w-full h-full flex items-center justify-center" @click="wheelClickMin(i)">
                        <span
                          :class="[
                            'font-mono text-2xl transition',
                            i === mIndex ? 'text-white font-semibold' : 'text-gray-500',
                          ]"
                        >
                          {{ pad2(v) }}
                        </span>
                      </button>
                    </div>
                  </div>

                  <div class="pointer-events-none absolute inset-0 flex items-center justify-center">
                    <div class="h-[44px] w-full rounded-xl bg-white/[0.06] border border-white/10" />
                  </div>
                </div>
              </div>

              <div class="mt-4 text-center text-lg font-mono font-semibold text-white">
                {{ selectedTimeText }}
              </div>
            </div>

            <!-- ON/OFF segmented -->
            <div class="bg-white/[0.03] border border-white/10 rounded-2xl p-2">
              <div class="relative grid grid-cols-2 gap-2">
                <!-- sliding pill -->
                <div
                  class="absolute top-1 bottom-1 left-1 w-[calc(50%-0.5rem)] rounded-2xl transition-transform duration-200"
                  :class="action === 'on' ? 'translate-x-0 bg-green-500/20 border border-green-500/25' : 'translate-x-full bg-white/[0.10] border border-white/15'"
                />
                <button
                  type="button"
                  class="relative z-10 py-3 rounded-2xl text-sm font-semibold transition"
                  :class="action === 'on' ? 'text-green-200' : 'text-gray-300 hover:text-white'"
                  @click="action = 'on'"
                >
                  ON
                </button>
                <button
                  type="button"
                  class="relative z-10 py-3 rounded-2xl text-sm font-semibold transition"
                  :class="action === 'off' ? 'text-white' : 'text-gray-300 hover:text-white'"
                  @click="action = 'off'"
                >
                  OFF
                </button>
              </div>
            </div>

            <!-- bottom safe padding -->
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
