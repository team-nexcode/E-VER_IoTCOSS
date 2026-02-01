<script setup lang="ts">
import { BarChart3, PlugZap, TrendingUp } from 'lucide-vue-next'

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

    <!-- 상위 전력 소비 디바이스 -->
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
</template>
