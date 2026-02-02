<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Brain, AlertTriangle, Zap, TrendingDown, Loader2, RefreshCw } from 'lucide-vue-next'

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

interface StandbyPowerDevice {
  device_mac: string
  device_name: string
  avg_standby_power_watts: number
  daily_waste_kwh: number
  monthly_waste_kwh: number
  monthly_waste_cost: number
}

interface AIReportData {
  anomalies: AnomalyDevice[]
  standby_power_devices: StandbyPowerDevice[]
  total_anomaly_count: number
  total_standby_waste_kwh: number
  total_standby_waste_cost: number
}

interface OpenAIAnalysis {
  summary: string
  recommendations: string[]
  anomaly_insights: string
  standby_insights: string
  estimated_savings: string
}

interface FullReport {
  report_data: AIReportData
  ai_analysis: OpenAIAnalysis
  generated_at: string
}

// ==================== State ====================

const loading = ref(false)
const error = ref<string | null>(null)
const report = ref<FullReport | null>(null)

// ==================== Methods ====================

async function loadAnalysis() {
  loading.value = true
  error.value = null
  
  try {
    const response = await fetch('/api/ai/full-report')
    if (!response.ok) {
      throw new Error(`분석 실패: ${response.statusText}`)
    }
    
    report.value = await response.json()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.'
    console.error('AI 분석 오류:', err)
  } finally {
    loading.value = false
  }
}

function getSeverityColor(severity: string) {
  switch (severity) {
    case 'high':
      return 'bg-red-500/20 text-red-400 border-red-500/30'
    case 'medium':
      return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
    default:
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
  }
}

function getSeverityLabel(severity: string) {
  switch (severity) {
    case 'high':
      return '높음'
    case 'medium':
      return '보통'
    default:
      return '낮음'
  }
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleString('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadAnalysis()
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
            v-for="anomaly in report.report_data.anomalies"
            :key="`${anomaly.device_mac}-${anomaly.timestamp}`"
            class="bg-gray-800/60 border border-gray-700 rounded-lg p-4"
          >
            <div class="flex items-start justify-between mb-2">
              <div>
                <div class="font-medium text-white">{{ anomaly.device_name }}</div>
                <div class="text-xs text-gray-500 mt-1">{{ formatDate(anomaly.timestamp) }}</div>
              </div>
              <span
                :class="[
                  'px-3 py-1 rounded-full text-xs font-medium border',
                  getSeverityColor(anomaly.severity)
                ]"
              >
                {{ getSeverityLabel(anomaly.severity) }}
              </span>
            </div>
            <div class="grid grid-cols-3 gap-4 text-sm">
              <div>
                <div class="text-gray-500 text-xs">현재 전류</div>
                <div class="text-white font-medium">{{ anomaly.current_amp.toFixed(2) }}A</div>
              </div>
              <div>
                <div class="text-gray-500 text-xs">예상 전류</div>
                <div class="text-white font-medium">{{ anomaly.expected_amp.toFixed(2) }}A</div>
              </div>
              <div>
                <div class="text-gray-500 text-xs">편차</div>
                <div class="text-red-400 font-medium">+{{ anomaly.deviation_percent }}%</div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8 text-gray-500">
          이상치가 감지되지 않았습니다.
        </div>
      </div>

      <!-- 대기전력 분석 -->
      <div class="bg-gradient-to-br from-gray-900/80 to-gray-900/40 border border-gray-800 rounded-2xl p-6">
        <h3 class="text-white font-semibold mb-3 flex items-center gap-2">
          <Zap class="w-5 h-5 text-yellow-400" />
          대기전력 낭비 상세
        </h3>
        <p class="text-sm text-gray-400 mb-4">
          {{ report.ai_analysis.standby_insights }}
        </p>

        <div v-if="report.report_data.standby_power_devices.length > 0" class="space-y-3">
          <div
            v-for="device in report.report_data.standby_power_devices"
            :key="device.device_mac"
            class="bg-gray-800/60 border border-gray-700 rounded-lg p-4"
          >
            <div class="font-medium text-white mb-3">{{ device.device_name }}</div>
            <div class="grid grid-cols-4 gap-4 text-sm">
              <div>
                <div class="text-gray-500 text-xs">평균 대기전력</div>
                <div class="text-white font-medium">{{ device.avg_standby_power_watts.toFixed(1) }}W</div>
              </div>
              <div>
                <div class="text-gray-500 text-xs">일일 낭비</div>
                <div class="text-white font-medium">{{ device.daily_waste_kwh.toFixed(3) }}kWh</div>
              </div>
              <div>
                <div class="text-gray-500 text-xs">월간 낭비</div>
                <div class="text-yellow-400 font-medium">{{ device.monthly_waste_kwh.toFixed(2) }}kWh</div>
              </div>
              <div>
                <div class="text-gray-500 text-xs">월간 비용</div>
                <div class="text-red-400 font-medium">{{ device.monthly_waste_cost.toLocaleString() }}원</div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8 text-gray-500">
          대기전력 낭비가 감지되지 않았습니다.
        </div>
      </div>

      <!-- AI 개선 권장사항 -->
      <div class="bg-gradient-to-br from-green-900/30 to-green-900/10 border border-green-500/20 rounded-2xl p-6">
        <h3 class="text-white font-semibold mb-4 flex items-center gap-2">
          <TrendingDown class="w-5 h-5 text-green-400" />
          개선 권장사항
        </h3>
        <ul class="space-y-3">
          <li
            v-for="(recommendation, index) in report.ai_analysis.recommendations"
            :key="index"
            class="flex items-start gap-3 text-gray-300"
          >
            <span class="w-6 h-6 flex items-center justify-center bg-green-500/20 text-green-400 rounded-full text-xs font-bold flex-shrink-0 mt-0.5">
              {{ index + 1 }}
            </span>
            <span>{{ recommendation }}</span>
          </li>
        </ul>
        <div class="mt-6 pt-6 border-t border-green-500/20">
          <p class="text-sm text-gray-400 mb-2">예상 절감 효과</p>
          <p class="text-green-400 font-medium">
            {{ report.ai_analysis.estimated_savings }}
          </p>
        </div>
      </div>

      <!-- 생성 시간 -->
      <div class="text-center text-xs text-gray-500">
        분석 생성 시간: {{ new Date(report.generated_at).toLocaleString('ko-KR') }}
      </div>
    </template>
  </div>
</template>
