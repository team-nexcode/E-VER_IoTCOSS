<script setup lang="ts">
import { computed } from 'vue'
import { BarChart3, PlugZap, TrendingUp, FileText, AlertTriangle, Activity } from 'lucide-vue-next'

// ==================== Types ====================

interface AnomalyDevice {
  device_mac: string
  device_name: string
  timestamp: string
  current_amp: number
  expected_amp: number
  deviation_percent: number
  severity: 'low' | 'medium' | 'high'
}

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
  <div class="space-y-6">
    <!-- 헤더 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-white">전력 분석</h2>
        <p class="text-sm text-gray-400 mt-1">
          AI 기반 전력 사용 패턴 분석 및 절감 제안
        </p>
      </div>
      <button
        @click="loadAnalysis"
        :disabled="loading"
        class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
      >
        <RefreshCw :class="['w-4 h-4', loading && 'animate-spin']" />
        <span>새로고침</span>
      </button>
    </div>

    <!-- 로딩 상태 -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
      <Loader2 class="w-12 h-12 text-blue-400 animate-spin mb-4" />
      <p class="text-gray-400">AI가 전력 데이터를 분석하고 있습니다...</p>
    </div>

    <!-- 에러 상태 -->
    <div
      v-else-if="error"
      class="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center"
    >
      <AlertTriangle class="w-12 h-12 text-red-400 mx-auto mb-3" />
      <p class="text-red-400 font-medium mb-2">분석 중 오류가 발생했습니다</p>
      <p class="text-sm text-gray-400">{{ error }}</p>
    </div>

    <!-- 분석 결과 -->
    <template v-else-if="report">
      <!-- AI 요약 -->
      <div class="bg-gradient-to-br from-blue-900/40 to-blue-900/20 border border-blue-500/30 rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <Brain class="w-6 h-6 text-blue-400" />
          <h3 class="text-xl font-semibold text-white">AI 분석 요약</h3>
        </div>
        <p class="text-gray-300 leading-relaxed">
          {{ report.ai_analysis.summary }}
        </p>
      </div>

      <!-- 통계 카드 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-gradient-to-br from-red-900/30 to-red-900/10 border border-red-500/20 rounded-xl p-5">
          <div class="flex items-center gap-2 mb-2">
            <AlertTriangle class="w-5 h-5 text-red-400" />
            <span class="text-sm text-gray-400">이상치 감지</span>
          </div>
          <div class="text-3xl font-bold text-white mb-1">
            {{ report.report_data.total_anomaly_count }}
          </div>
          <div class="text-xs text-gray-500">건</div>
        </div>

        <div class="bg-gradient-to-br from-yellow-900/30 to-yellow-900/10 border border-yellow-500/20 rounded-xl p-5">
          <div class="flex items-center gap-2 mb-2">
            <Zap class="w-5 h-5 text-yellow-400" />
            <span class="text-sm text-gray-400">대기전력 낭비</span>
          </div>
          <div class="text-3xl font-bold text-white mb-1">
            {{ report.report_data.total_standby_waste_kwh.toFixed(1) }}
          </div>
          <div class="text-xs text-gray-500">kWh/월</div>
        </div>

        <div class="bg-gradient-to-br from-green-900/30 to-green-900/10 border border-green-500/20 rounded-xl p-5">
          <div class="flex items-center gap-2 mb-2">
            <TrendingDown class="w-5 h-5 text-green-400" />
            <span class="text-sm text-gray-400">예상 낭비 비용</span>
          </div>
          <div class="text-3xl font-bold text-white mb-1">
            {{ report.report_data.total_standby_waste_cost.toLocaleString() }}
          </div>
          <div class="text-xs text-gray-500">원/월</div>
        </div>
      </div>

      <!-- 이상치 분석 -->
      <div class="bg-gradient-to-br from-gray-900/80 to-gray-900/40 border border-gray-800 rounded-2xl p-6">
        <h3 class="text-white font-semibold mb-3 flex items-center gap-2">
          <AlertTriangle class="w-5 h-5 text-red-400" />
          이상치 감지 상세
        </h3>
        <p class="text-sm text-gray-400 mb-4">
          {{ report.ai_analysis.anomaly_insights }}
        </p>

        <div v-if="report.report_data.anomalies.length > 0" class="space-y-3">
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
                {{ getSeverityLabel(anomaly.severity) }}
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
        <div v-else class="text-center py-8 text-gray-500">
          이상치가 감지되지 않았습니다.
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
