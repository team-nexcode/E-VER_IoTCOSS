<script setup lang="ts">
import { computed } from 'vue'
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

const maxUsage = Math.max(...hourlyUsage.map(h => h.value))

/**
 * 🔹 리포트 입력(백엔드 연결용)
 * - 기존 기능 영향 없게: report prop이 있으면 사용, 없으면 더미 표시
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
const isRisky = computed(() => standbyHigh.value || anomaliesHigh.value)

const statusBadge = computed(() => {
  return isRisky.value
    ? { text: '주의', cls: 'bg-amber-500/10 text-amber-200 border-amber-500/20' }
    : { text: '정상', cls: 'bg-emerald-500/10 text-emerald-200 border-emerald-500/20' }
})

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

const recommendations = computed(() => {
  const list: { tone: 'warn' | 'ok'; title: string; desc: string }[] = []

  if (standbyHigh.value) {
    list.push({
      tone: 'warn',
      title: '미사용 시간대 차단 권장',
      desc: 'Standby 누적이 커서 스케줄/타이머 기반 차단을 추천합니다.',
    })
  } else {
    list.push({
      tone: 'ok',
      title: 'Standby 상태 양호',
      desc: '대기전력 수준이 안정적입니다.',
    })
  }

  if (anomaliesHigh.value) {
    list.push({
      tone: 'warn',
      title: '이상치 원인 점검 필요',
      desc: '센서 값 튐/부하 변동/릴레이 접점 상태를 우선 확인해 주세요.',
    })
  } else if (report.value.anomalies.count > 0) {
    list.push({
      tone: 'ok',
      title: '이상치 소량(관찰)',
      desc: '즉시 조치보다는 추세 관찰을 권장합니다.',
    })
  } else {
    list.push({
      tone: 'ok',
      title: '이상치 없음',
      desc: '측정값이 안정적입니다.',
    })
  }

  return list
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

    <!-- ✅ 좌(리포트) / 우(상위 디바이스) -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 왼쪽: AI 분석 리포트 -->
      <div class="lg:col-span-2 bg-gradient-to-br from-gray-900/80 to-gray-900/40 border border-gray-800 rounded-2xl p-6">
        <!-- 헤더 -->
        <div class="flex items-start justify-between gap-4">
          <div class="min-w-0">
            <h3 class="text-white font-semibold flex items-center gap-2">
              <Sparkles class="w-5 h-5 text-purple-300" />
              AI분석 리포트
            </h3>
            <p class="text-xs text-gray-400 mt-1">
              최근 <span class="text-gray-200 font-semibold">{{ report.hours }}</span>시간 기준 요약 및 권장 조치
            </p>
          </div>

          <div class="flex items-center gap-2 flex-shrink-0">
            <span class="text-xs px-2.5 py-1 rounded-full border" :class="statusBadge.cls">
              {{ statusBadge.text }}
            </span>
            <span class="text-xs px-2.5 py-1 rounded-full border bg-blue-500/10 text-blue-200 border-blue-500/20">
              상태 {{ report.state_now.state }}
            </span>
          </div>
        </div>

        <!-- 핵심 포인트 칩 -->
        <div class="mt-4 flex flex-wrap gap-2">
          <span
            class="text-[11px] px-2.5 py-1 rounded-full border"
            :class="standbyHigh ? 'bg-amber-500/10 text-amber-200 border-amber-500/20' : 'bg-gray-500/10 text-gray-200 border-gray-500/20'"
          >
            standby {{ report.waste.standby_wh.toFixed(2) }}Wh (기준 50Wh)
          </span>
          <span
            class="text-[11px] px-2.5 py-1 rounded-full border"
            :class="anomaliesHigh ? 'bg-amber-500/10 text-amber-200 border-amber-500/20' : 'bg-gray-500/10 text-gray-200 border-gray-500/20'"
          >
            이상치 {{ report.anomalies.count }}건 (기준 3건)
          </span>
          <span
            v-if="!isRisky"
            class="text-[11px] px-2.5 py-1 rounded-full border bg-emerald-500/10 text-emerald-200 border-emerald-500/20"
          >
            특이사항 없음
          </span>
        </div>

        <!-- 숫자 타일 -->
        <div class="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div
            class="rounded-2xl border bg-gray-900/35 px-4 py-4"
            :class="standbyHigh ? 'border-amber-500/25' : 'border-gray-800'"
          >
            <div class="text-[11px] text-gray-400 flex items-center gap-2">
              <Activity class="w-4 h-4 text-sky-300" />
              standby 추정
            </div>
            <div class="mt-2 text-2xl font-bold text-white tabular-nums">
              {{ report.waste.standby_wh.toFixed(2) }}
              <span class="text-xs font-medium text-gray-400 ml-1">Wh</span>
            </div>
            <div class="mt-1 text-[11px] text-gray-500">임계 50Wh 이상 주의</div>
          </div>

          <div
            class="rounded-2xl border bg-gray-900/35 px-4 py-4"
            :class="anomaliesHigh ? 'border-amber-500/25' : 'border-gray-800'"
          >
            <div class="text-[11px] text-gray-400 flex items-center gap-2">
              <AlertTriangle class="w-4 h-4 text-amber-300" />
              이상치
            </div>
            <div class="mt-2 text-2xl font-bold text-white tabular-nums">
              {{ report.anomalies.count }}
              <span class="text-xs font-medium text-gray-400 ml-1">건</span>
            </div>
            <div class="mt-1 text-[11px] text-gray-500">임계 3건 이상 점검 권장</div>
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
            <div class="mt-1 text-[11px] text-gray-500">최근 데이터 기반</div>
          </div>
        </div>

        <!-- ✅ AI 코멘트 (애플 느낌: 유리질감 + 얇은 라인 + 미니멀) -->
        <div
          class="mt-4 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md
                 shadow-[0_10px_30px_rgba(0,0,0,0.25)] px-4 py-4"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span
                class="w-1.5 h-1.5 rounded-full"
                :class="isRisky ? 'bg-amber-300' : 'bg-emerald-300'"
              />
              <div class="text-xs font-semibold text-white/90 tracking-tight">
                AI 코멘트
              </div>
            </div>

            <div class="flex items-center gap-2">
              <span
                class="text-[11px] px-2 py-0.5 rounded-full border border-white/10 bg-black/20 text-white/70"
              >
                {{ report.state_now.state }}
              </span>
              <span class="text-[11px] px-2 py-0.5 rounded-full border" :class="statusBadge.cls">
                {{ statusBadge.text }}
              </span>
            </div>
          </div>

          <div class="mt-3 h-px bg-white/10"></div>

          <p class="mt-3 text-[14px] leading-relaxed text-white/85 break-words">
            {{ summary }}
          </p>
        </div>

        <!-- 권장 조치 (그대로) -->
        <div class="mt-4">
          <div class="text-xs text-gray-400">권장 조치</div>
          <div class="mt-2 space-y-2">
            <div
              v-for="(it, idx) in recommendations"
              :key="idx"
              class="rounded-2xl border px-4 py-3"
              :class="it.tone === 'warn' ? 'border-amber-500/25 bg-amber-500/10' : 'border-emerald-500/25 bg-emerald-500/10'"
            >
              <div class="flex items-start gap-3">
                <AlertTriangle v-if="it.tone === 'warn'" class="w-4 h-4 mt-0.5 text-amber-300 flex-shrink-0" />
                <CheckCircle2 v-else class="w-4 h-4 mt-0.5 text-emerald-300 flex-shrink-0" />
                <div class="min-w-0">
                  <div class="text-sm font-semibold text-white">{{ it.title }}</div>
                  <div class="text-sm text-gray-200 mt-0.5 leading-relaxed">{{ it.desc }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 오른쪽: 상위 전력 소비 디바이스 (그대로) -->
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
