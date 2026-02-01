<script setup lang="ts">
import { Zap, Thermometer, Droplets, Power, Wifi, WifiOff } from 'lucide-vue-next'
import { useDeviceStore } from '@/stores/device'
import { storeToRefs } from 'pinia'
import PowerChart from './PowerChart.vue'

const props = defineProps<{
  selectedDeviceId: number | null
}>()

const emit = defineEmits<{
  selectDevice: [id: number | null]
}>()

const store = useDeviceStore()
const { devices } = storeToRefs(store)
</script>

<template>
  <div class="h-full flex flex-col bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
    <!-- 헤더 -->
    <div class="flex-shrink-0 px-4 py-3 border-b border-gray-800">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-white">디바이스 목록</h3>
        <div class="flex items-center gap-1.5">
          <div class="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
          <span class="text-[11px] text-gray-400">
            온라인 <span class="text-green-400 font-semibold">{{ devices.filter((d) => d.isOnline).length }}</span>
            <span class="text-gray-600">/{{ devices.length }}</span>
          </span>
        </div>
      </div>
      <p class="text-[10px] text-gray-500 mt-0.5">클릭하여 구조도에서 위치 확인</p>
    </div>

    <!-- 디바이스 카드 목록 (스크롤) -->
    <div class="flex-1 min-h-0 overflow-y-auto p-3 space-y-3">
      <div
        v-for="device in devices"
        :key="device.id"
        :class="[
          'rounded-xl border px-4 py-4 cursor-pointer transition-all duration-200',
          props.selectedDeviceId === device.id
            ? 'bg-sky-500/10 border-sky-500/40 shadow-lg shadow-sky-500/5'
            : 'bg-gray-800/40 border-gray-700/50 hover:bg-gray-800/70 hover:border-gray-600',
        ]"
        @click="emit('selectDevice', props.selectedDeviceId === device.id ? null : device.id)"
      >
        <!-- 디바이스 헤더 -->
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2 min-w-0">
            <Wifi v-if="device.isOnline" class="w-3.5 h-3.5 text-green-400 flex-shrink-0" />
            <WifiOff v-else class="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
            <span
              :class="['text-sm font-medium truncate', props.selectedDeviceId === device.id ? 'text-sky-300' : 'text-white']"
            >
              {{ device.name }}
            </span>
          </div>
          <span class="text-[10px] text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded-full flex-shrink-0">
            {{ device.location }}
          </span>
        </div>

        <!-- 전력 / 온도 / 습도 -->
        <div class="flex items-center gap-4 mb-3 flex-wrap">
          <div class="flex items-center gap-1.5">
            <Zap class="w-3.5 h-3.5 text-yellow-400" />
            <span v-if="device.isOnline"
              :class="[
                'text-xs font-semibold',
                (device.currentPower * 220) > 500 ? 'text-red-400' : device.currentPower > 0 ? 'text-yellow-400' : 'text-gray-500',
              ]"
            >
              {{ (device.currentPower * 220).toFixed(1) }}W / {{ device.currentPower.toFixed(3) }}A
            </span>
            <span v-else class="text-xs font-semibold text-gray-600">--</span>
          </div>
          <div class="flex items-center gap-1.5">
            <Thermometer class="w-3.5 h-3.5 text-orange-400" />
            <span v-if="device.isOnline"
              :class="[
                'text-xs font-semibold',
                device.temperature > 40 ? 'text-red-400' : device.temperature > 35 ? 'text-orange-400' : 'text-green-400',
              ]"
            >
              {{ device.temperature.toFixed(1) }}°C
            </span>
            <span v-else class="text-xs font-semibold text-gray-600">--</span>
          </div>
          <div class="flex items-center gap-1.5">
            <Droplets class="w-3.5 h-3.5 text-sky-400" />
            <span v-if="device.isOnline" class="text-xs font-semibold text-sky-400">
              {{ device.humidity.toFixed(1) }}%
            </span>
            <span v-else class="text-xs font-semibold text-gray-600">--</span>
          </div>
        </div>

        <!-- On/Off 상태 표시 -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <Power class="w-3.5 h-3.5 text-blue-400" />
            <span class="text-[10px] text-gray-400">전원</span>
          </div>
          <span
            :class="[
              'flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-medium',
              !device.isOnline
                ? 'bg-gray-700 text-gray-500'
                : device.isActive
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                  : 'bg-gray-700/50 text-gray-400 border border-gray-600/30',
            ]"
          >
            <div :class="['w-1.5 h-1.5 rounded-full', device.isActive && device.isOnline ? 'bg-green-400' : 'bg-gray-500']" />
            {{ !device.isOnline ? '오프라인' : device.isActive ? 'ON' : 'OFF' }}
          </span>
        </div>
      </div>
    </div>

    <!-- 하단: 일별 전력량 차트 -->
    <div class="flex-shrink-0 h-44 border-t border-gray-800">
      <PowerChart :selected-device-id="props.selectedDeviceId" />
    </div>
  </div>
</template>
