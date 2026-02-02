<script setup lang="ts">
import { computed } from 'vue'
import { BarChart3, PlugZap, TrendingUp, FileText, AlertTriangle, Activity } from 'lucide-vue-next'

// 🔹 시간대별 평균 전력 사용량 (kWh) - 더미 데이터
const hourlyUsage = [
  { hour: '0', value: 1.2 },
  { hour: '3', value: 0.8 },
  { hour: '6', value: 1.5 },
  { hour: '9', value: 3.2 },
  { hour: '12', value: 4.1 },
  { hour: '15', value: 3.6 },
  { hour: '18', value: 5.4 },
  { hour: '21', value: 4.8 },
]

// 🔹 상위 3개 전력 소비 디바이스
const topDevices = [
  { name: '온풍기', usage: 38 },
  { name: '전기히터', usage: 22 },
  { name: 'TV', usage: 11 },
]

const maxUsage = Math.max(...hourlyUsage.map((h) => h.value))

/**
 * 🔹 자동 리포트 입력(백엔드 연결용)
 * - 기존 기능 영향 없게: props로 들어오면 사용, 없으면 더미로 표시
 */
type AnalysisReport = {
  hours: number
  waste: { standby_wh: number }
  anomalies: { count: number }
  state_now: { state: string }
}

const props = defineProps<{
  report?: AnalysisReport
}>()

const report = computed<AnalysisReport>(() => {
  return (
    props.report ?? {
      hours: 6,
      waste: { standby_wh: 58.32 },
      anomalies: { count: 4 },
      state_now: { state: 'ON' },
    }
  )
})

const standbyHigh = computed(() => report.value.waste.standby_wh >= 50)
const anomaliesHigh = computed(() => report.value.anomalies.count >= 3)

// ✅ 사용자 스크립트 기반 summary
const summary = computed(() => {
  const hours = report.value.hours
  const waste = report.value.waste
  const anomalies = report.value.anomalies
  const state_now = report.value.state_now

  let s =
    `최근 ${hours}시간 기준 standby 추정 ${waste.standby_wh.toFixed(2)}Wh, ` +
    `이상치 ${anomalies.count}건, 현재 상태 ${state_now.state}.`

  if (waste.standby_wh >= 50) s += ' standby 낭비가 큰 편이라 미사용 시 차단을 권장.'
  if (anomalies.count >= 3) s += ' 이상치가 반복되어 센서/부하/릴레이 점검 권장.'
  return s
})

const actions = computed(() => {
  const items: string[] = []
  if (standbyHigh.value) items.push('미사용 시간대 자동 차단(스케줄/타이머) 권장')
  if (anomaliesHigh.value) items.push('센서 값 튐/부하 변동/릴레이 상태 점검 권장')
  if (items.length === 0) items.push('특이사항 없음: 현재 운영 유지')
  return items
})
</script>

<template>
  <div class="space-y-10">
    <!-- 헤더 -->
    <div>
      <h2 class="text-2xl font-bold text-white">전력 분석</h2>
      <p class="text-sm text-gray-400 mt-1">
        시간대별 사용 패턴과 주요 전력 소비 기기를 분석합니다
      </p>
    </div>

    <!-- 시간대별 평균 전력 사용량 -->
    <div class="bg-gradient-to-br from-gray-900/80 to-gray-900/40 border border-gray-800 rounded-2xl p-6">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-white font-semibold flex items-center gap-2">
          <BarChart3 class="w-5 h-5 text-blue-400" />
          시간대별 평균 전력 사용량
        </h3>
        <span class="text-xs text-blue-400 flex items-center gap-1">
          <TrendingUp class="w-4 h-4" />
          kWh
        </span>
      </div>

      <div class="flex items-end gap-3 h-44">
        <div
          v-for="item in hourlyUsage"
          :key="item.hour"
          class="flex-1 flex flex-col items-center group"
        >
          <div
            class="w-full rounded-lg bg-gradient-to-t from-blue-600 to-blue-400 transition-all"
            :style="{ height: `${(item.value / maxUsage) * 100}%` }"
          />
          <span class="text-[11px] text-gray-400 mt-2">{{ item.hour }}시</span>
          <span class="text-[11px] text-gray-500 opacity-0 group-hover:opacity-100 transition">
            {{ item.value }} kWh
          </span>
        </div>
      </div>

      <div class="mt-5 text-xs text-gray-400">
        전력 사용 피크 시간대는
        <span class="text-blue-400 font-semibold">18~21시</span>
        입니다.
      </div>
    </div>

    <!-- 자동 분석 리포트 (summary 스크립트 기반) -->
    <div class="bg-gradient-to-br from-gray-900/80 to-gray-900/40 border border-gray-800 rounded-2xl p-6">
      <div class="flex items-start justify-between gap-4 mb-4">
        <h3 class="text-white font-semibold flex items-center gap-2">
          <FileText class="w-5 h-5 text-purple-300" />
          자동 분석 리포트
        </h3>

        <div class="flex items-center gap-2">
          <span
            class="text-xs px-2.5 py-1 rounded-full border"
            :class="standbyHigh ? 'bg-amber-500/10 text-amber-200 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-200 border-emerald-500/20'"
          >
            standby {{ standbyHigh ? '주의' : '양호' }}
          </span>
          <span
            class="text-xs px-2.5 py-1 rounded-full border"
            :class="anomaliesHigh ? 'bg-amber-500/10 text-amber-200 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-200 border-emerald-500/20'"
          >
            이상치 {{ anomaliesHigh ? '주의' : '양호' }}
          </span>
          <span class="text-xs px-2.5 py-1 rounded-full border bg-blue-500/10 text-blue-200 border-blue-500/20">
            상태 {{ report.state_now.state }}
          </span>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div class="rounded-xl border border-gray-800 bg-gray-900/40 px-4 py-3">
          <div class="text-[11px] text-gray-400 flex items-center gap-2">
            <Activity class="w-4 h-4 text-sky-300" />
            standby 추정
          </div>
          <div class="mt-1 text-white font-semibold">
            {{ report.waste.standby_wh.toFixed(2) }} <span class="text-xs text-gray-400">Wh</span>
          </div>
        </div>

        <div class="rounded-xl border border-gray-800 bg-gray-900/40 px-4 py-3">
          <div class="text-[11px] text-gray-400 flex items-center gap-2">
            <AlertTriangle class="w-4 h-4 text-amber-300" />
            이상치
          </div>
          <div class="mt-1 text-white font-semibold">
            {{ report.anomalies.count }} <span class="text-xs text-gray-400">건</span>
          </div>
        </div>

        <div class="rounded-xl border border-gray-800 bg-gray-900/40 px-4 py-3">
          <div class="text-[11px] text-gray-400 flex items-center gap-2">
            <FileText class="w-4 h-4 text-purple-300" />
            분석 구간
          </div>
          <div class="mt-1 text-white font-semibold">
            최근 {{ report.hours }}시간
          </div>
        </div>
      </div>

      <div class="mt-4 rounded-xl border border-gray-800 bg-gray-900/30 p-4">
        <div class="text-[11px] text-gray-400 mb-1">요약</div>
        <p class="text-sm text-gray-200 leading-relaxed">
          {{ summary }}
        </p>
      </div>

      <div class="mt-3 space-y-2">
        <div class="text-[11px] text-gray-400">권장 조치</div>

        <div
          v-for="(t, i) in actions"
          :key="i"
          class="rounded-xl border border-gray-800 bg-gray-900/25 px-4 py-3 text-sm text-gray-200"
        >
          {{ t }}
        </div>
      </div>
    </div>

    <!-- 상위 전력 소비 디바이스 -->
    <div class="bg-gradient-to-br from-gray-900/80 to-gray-900/40 border border-gray-800 rounded-2xl p-6">
      <h3 class="text-white font-semibold mb-4 flex items-center gap-2">
        <PlugZap class="w-5 h-5 text-yellow-400" />
        전력 소비 상위 디바이스
      </h3>

      <!-- 3개 창을 컴팩트하게(데스크탑 3열) -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div
          v-for="(device, index) in topDevices"
          :key="device.name"
          class="bg-gray-800/60 border border-gray-700 rounded-xl px-4 py-3"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2 min-w-0">
              <span
                class="w-6 h-6 flex items-center justify-center rounded-full text-[11px] font-bold flex-shrink-0"
                :class="index === 0
                  ? 'bg-red-500/20 text-red-400'
                  : index === 1
                  ? 'bg-yellow-500/20 text-yellow-400'
                  : 'bg-blue-500/20 text-blue-400'"
              >
                {{ index + 1 }}
              </span>
              <span class="text-white font-medium text-sm truncate">{{ device.name }}</span>
            </div>
            <span class="text-sm text-gray-300 flex-shrink-0">
              {{ device.usage }}%
            </span>
          </div>

          <!-- usage bar -->
          <div class="h-2 w-full bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full"
              :class="index === 0
                ? 'bg-red-400'
                : index === 1
                ? 'bg-yellow-400'
                : 'bg-blue-400'"
              :style="{ width: device.usage + '%' }"
            />
          </div>
        </div>
      </div>

      <p class="text-xs text-gray-400 mt-4">
        상위 3개 디바이스가 전체 전력의
        <span class="text-white font-semibold">
          {{ topDevices.reduce((a, b) => a + b.usage, 0) }}%
        </span>
        를 소비하고 있습니다
      </p>
    </div>
  </div>
</template>
