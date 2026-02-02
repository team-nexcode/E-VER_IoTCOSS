<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import {
  BarChart3,
  PlugZap,
  TrendingUp,
  FileText,
  AlertTriangle,
  Activity,
  CheckCircle2,
  Sparkles,
} from 'lucide-vue-next'

// 🔹 시간대별 평균 전력 사용량 (kWh) - 실시간 데이터
const hourlyUsage = ref<Array<{ hour: string; value: number }>>([])

// 🔹 상위 3개 전력 소비 디바이스 - 실시간 데이터
const topDevices = ref<Array<{ name: string; usage: number }>>([])

const maxUsage = computed(() => Math.max(...hourlyUsage.value.map(h => h.value), 1))

/**
 * 🔹 AI 리포트 데이터 (실시간)
 */
type AnalysisReport = {
  hours: number
  device_count: number
  total_anomaly_count: number
  total_standby_wh: number
  total_monthly_kwh: number
  total_monthly_cost: number
  devices: Array<{
    device_name: string
    anomaly_count: number
    standby_wh: number
    state: string
  }>
  openai_analysis?: {
    summary: string
    recommendations: string[]
    anomaly_insights: string
    standby_insights: string
    estimated_savings: string
  }
}

const report = ref<AnalysisReport>({
  hours: 24,
  device_count: 0,
  total_anomaly_count: 0,
  total_standby_wh: 0,
  total_monthly_kwh: 0,
  total_monthly_cost: 0,
  devices: []
})

const loading = ref(false)
const error = ref<string | null>(null)

// AI 리포트 가져오기 (모든 기기 종합 분석)
async function fetchAIReport() {
  loading.value = true
  error.value = null
  
  try {
    // 백엔드를 통해 모든 기기의 AI 서버 + OpenAI 분석 받기
    const response = await axios.get('http://iotcoss.nexcode.kr:8000/api/ai/analyze-ai-server', {
      params: { hours: 24 }
    })
    
    const data = response.data
    
    report.value = {
      hours: data.hours,
      device_count: data.device_count,
      total_anomaly_count: data.total_anomaly_count,
      total_standby_wh: data.total_standby_wh,
      total_monthly_kwh: data.total_monthly_kwh,
      total_monthly_cost: data.total_monthly_cost,
      devices: data.devices,
      openai_analysis: data.openai_available ? data.openai_analysis : undefined
    }
    
    // 시간대별 사용량 업데이트
    if (data.hourly_usage && data.hourly_usage.length > 0) {
      hourlyUsage.value = data.hourly_usage
    }
    
    // 상위 디바이스 업데이트
    if (data.top_devices && data.top_devices.length > 0) {
      topDevices.value = data.top_devices
    }
  } catch (e: any) {
    console.error('AI 리포트 로드 실패:', e)
    error.value = e.response?.data?.detail || e.message || '리포트를 불러올 수 없습니다'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAIReport()
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

    <!-- 로딩/에러 상태 -->
    <div v-if="loading" class="bg-gradient-to-br from-gray-900/80 to-gray-900/40 border border-gray-800 rounded-2xl p-6">
      <div class="flex items-center justify-center gap-3">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
        <span class="text-gray-400">AI 분석 리포트 로딩 중...</span>
      </div>
    </div>

    <div v-if="error" class="bg-red-500/10 border border-red-500/20 rounded-2xl p-4">
      <div class="flex items-center gap-2">
        <AlertTriangle class="w-5 h-5 text-red-400" />
        <span class="text-red-200">{{ error }}</span>
      </div>
    </div>

    <!-- 시간대별 평균 전력 사용량 -->
    <!-- ⚠️ 사용자 요청: 이 창은 건드리지 않음(원본 그대로) -->
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
          v-if="hourlyUsage.length === 0"
          class="flex items-center justify-center w-full h-full text-gray-500 text-sm"
        >
          데이터를 불러오는 중...
        </div>
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

      <div class="mt-5 text-xs text-gray-400" v-if="hourlyUsage.length > 0">
        전력 사용 피크 시간대 분석 완료
      </div>
    </div>

    <!-- ✅ 좌(리포트) / 우(상위 디바이스) -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 왼쪽: AI 분석 리포트 (읽기 쉽게) -->
      <div class="lg:col-span-2 bg-gradient-to-br from-gray-900/80 to-gray-900/40 border border-gray-800 rounded-2xl p-6">
        <!-- 헤더 -->
        <div class="flex items-start justify-between gap-4">
          <div class="min-w-0">
            <h3 class="text-white font-semibold flex items-center gap-2">
              <Sparkles class="w-5 h-5 text-purple-300" />
              AI분석 리포트
            </h3>
            <p class="text-xs text-gray-400 mt-1">
              최근 <span class="text-gray-200 font-semibold">{{ report.hours }}</span>시간 기준 {{ report.device_count }}개 기기 종합 분석
            </p>
          </div>
        </div>

        <!-- 핵심 포인트 칩 -->
        <div class="mt-4 flex flex-wrap gap-2">
          <span class="text-[11px] px-2.5 py-1 rounded-full border bg-gray-500/10 text-gray-200 border-gray-500/20">
            standby {{ report.total_standby_wh.toFixed(2) }}Wh
          </span>
          <span class="text-[11px] px-2.5 py-1 rounded-full border bg-gray-500/10 text-gray-200 border-gray-500/20">
            이상치 {{ report.total_anomaly_count }}건
          </span>
        </div>

        <!-- 숫자 타일 (한눈에) -->
        <div class="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div class="rounded-2xl border border-gray-800 bg-gray-900/35 px-4 py-4">
            <div class="text-[11px] text-gray-400 flex items-center gap-2">
              <Activity class="w-4 h-4 text-sky-300" />
              standby 추정
            </div>
            <div class="mt-2 text-2xl font-bold text-white tabular-nums">
              {{ report.total_standby_wh.toFixed(2) }}
              <span class="text-xs font-medium text-gray-400 ml-1">Wh</span>
            </div>
          </div>

          <div class="rounded-2xl border border-gray-800 bg-gray-900/35 px-4 py-4">
            <div class="text-[11px] text-gray-400 flex items-center gap-2">
              <AlertTriangle class="w-4 h-4 text-amber-300" />
              이상치
            </div>
            <div class="mt-2 text-2xl font-bold text-white tabular-nums">
              {{ report.total_anomaly_count }}
              <span class="text-xs font-medium text-gray-400 ml-1">건</span>
            </div>
          </div>

          <div class="rounded-2xl border border-gray-800 bg-gray-900/35 px-4 py-4">
            <div class="text-[11px] text-gray-400 flex items-center gap-2">
              <FileText class="w-4 h-4 text-purple-300" />
              분석 구간
            </div>
            <div class="mt-2 text-2xl font-bold text-white tabular-nums">
              {{ report.hours }}
              <span class="text-xs font-medium text-gray-400 ml-1">시간</span>
            </div>
          </div>
        </div>

        <!-- AI 코멘트 (긴 문장은 여기에 모아 가독성 확보) -->
        <div class="mt-4 rounded-2xl border border-gray-800 bg-gray-900/30 p-4">
          <div class="flex items-start gap-3">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center border bg-purple-500/10 border-purple-500/20 flex-shrink-0">
              <Sparkles class="w-4 h-4 text-purple-300" />
            </div>

            <div class="min-w-0">
              <div class="text-sm font-semibold text-white">AI 코멘트</div>
              <p class="text-sm text-gray-200 mt-1 leading-relaxed break-words">
                {{ report.openai_analysis?.summary || '분석 데이터를 불러오는 중입니다...' }}
              </p>
            </div>
          </div>
        </div>

        <!-- 권장사항 (OpenAI 분석) -->
        <div v-if="report.openai_analysis?.recommendations?.length" class="mt-4">
          <div class="text-xs text-gray-400 mb-2">AI 권장사항</div>
          <div class="space-y-2">
            <div
              v-for="(rec, idx) in report.openai_analysis.recommendations"
              :key="idx"
              class="rounded-2xl border border-purple-500/25 bg-purple-500/10 px-4 py-3"
            >
              <div class="flex items-start gap-3">
                <CheckCircle2 class="w-4 h-4 mt-0.5 text-purple-300 flex-shrink-0" />
                <p class="text-sm text-gray-200 leading-relaxed">{{ rec }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 오른쪽: 상위 전력 소비 디바이스 (기존 내용 유지, 위치만 오른쪽) -->
      <div class="bg-gradient-to-br from-gray-900/80 to-gray-900/40 border border-gray-800 rounded-2xl p-6">
        <h3 class="text-white font-semibold mb-6 flex items-center gap-2">
          <PlugZap class="w-5 h-5 text-yellow-400" />
          전력 소비 상위 디바이스
        </h3>

        <div class="space-y-4">
          <div
            v-for="(device, index) in topDevices"
            :key="device.name"
            class="bg-gray-800/60 border border-gray-700 rounded-xl p-4"
          >
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-3">
                <span
                  class="w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold"
                  :class="index === 0
                    ? 'bg-red-500/20 text-red-400'
                    : index === 1
                    ? 'bg-yellow-500/20 text-yellow-400'
                    : 'bg-blue-500/20 text-blue-400'"
                >
                  {{ index + 1 }}
                </span>
                <span class="text-white font-medium">{{ device.name }}</span>
              </div>
              <span class="text-sm text-gray-300">
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

        <p class="text-xs text-gray-400 mt-5">
          상위 3개 디바이스가 전체 전력의
          <span class="text-white font-semibold">
            {{ topDevices.reduce((a, b) => a + b.usage, 0) }}%
          </span>
          를 소비하고 있습니다
        </p>
      </div>
    </div>
  </div>
</template>
