<script setup lang="ts">
import { BarChart3, PlugZap } from 'lucide-vue-next'

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
  { name: '에어컨', usage: 38 },
  { name: '전기히터', usage: 22 },
  { name: 'TV', usage: 11 },
]

const maxUsage = Math.max(...hourlyUsage.map(h => h.value))
</script>

<template>
  <div class="space-y-8">
    <!-- 헤더 -->
    <div>
      <h2 class="text-2xl font-bold text-white">전력 분석</h2>
      <p class="text-sm text-gray-500 mt-1">
        시간대별 사용 패턴과 주요 소비 기기를 분석합니다
      </p>
    </div>

    <!-- 시간대별 평균 전력 사용량 -->
    <div class="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
      <h3 class="text-white font-semibold mb-4 flex items-center gap-2">
        <BarChart3 class="w-5 h-5" />
        시간대별 평균 전력 사용량
      </h3>

      <div class="flex items-end gap-4 h-40">
        <div
          v-for="item in hourlyUsage"
          :key="item.hour"
          class="flex-1 flex flex-col items-center"
        >
          <div
            class="w-full bg-blue-500/70 rounded-t-lg transition-all"
            :style="{ height: `${(item.value / maxUsage) * 100}%` }"
          />
          <span class="text-xs text-gray-400 mt-2">{{ item.hour }}시</span>
        </div>
      </div>

      <p class="text-xs text-gray-500 mt-4">
        최근 평균 기준, <span class="text-blue-400">18~21시</span> 전력 사용이 가장 높습니다
      </p>
    </div>

    <!-- 상위 전력 소비 디바이스 -->
    <div class="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
      <h3 class="text-white font-semibold mb-4 flex items-center gap-2">
        <PlugZap class="w-5 h-5" />
        전력 소비 상위 디바이스
      </h3>

      <div class="space-y-3">
        <div
          v-for="(device, index) in topDevices"
          :key="device.name"
          class="flex items-center justify-between bg-gray-800 rounded-xl px-4 py-3"
        >
          <div class="flex items-center gap-3">
            <span
              class="w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold"
              :class="index === 0
                ? 'bg-red-500/20 text-red-400'
                : index === 1
                ? 'bg-yellow-500/20 text-yellow-400'
                : 'bg-blue-500/20 text-blue-400'"
            >
              {{ index + 1 }}
            </span>
            <span class="text-white">{{ device.name }}</span>
          </div>

          <span class="text-gray-400 text-sm">
            {{ device.usage }}%
          </span>
        </div>
      </div>

      <p class="text-xs text-gray-500 mt-4">
        상위 3개 기기가 전체 전력의 {{ topDevices.reduce((a, b) => a + b.usage, 0) }}%를 차지합니다
      </p>
    </div>
  </div>
</template>

