<script setup lang="ts">
import { Power, Thermometer, Droplets, Zap, Wifi, WifiOff } from 'lucide-vue-next'
import type { Device } from '@/types/device'

const props = defineProps<{
  device: Device
  x: number
  y: number
}>()

const isLeft = props.x > 50
const isTop = props.y > 60
</script>

<template>
  <div
    class="absolute z-30 pointer-events-auto"
    :style="{
      left: `${props.x}%`,
      top: `${props.y}%`,
      transform: `translate(${isLeft ? '-100%' : '0'}, ${isTop ? '-100%' : '0'})`,
    }"
  >
    <!-- 콘센트 마커 -->
    <div class="relative">
      <!-- 연결선 -->
      <div
        :class="['absolute w-px h-8', props.device.isOnline ? (props.device.isActive ? 'bg-green-500' : 'bg-gray-600') : 'bg-red-500']"
        :style="{
          left: isLeft ? '100%' : '0',
          top: isTop ? '100%' : '-32px',
        }"
      />

      <!-- 말풍선 팝업 -->
      <div
        :class="[
          'w-44 sm:w-52 rounded-xl border shadow-2xl backdrop-blur-sm transition-all duration-300',
          props.device.isOnline
            ? props.device.isActive
              ? 'bg-gray-900/95 border-green-500/30 shadow-green-500/10'
              : 'bg-gray-900/95 border-gray-600/30'
            : 'bg-gray-900/95 border-red-500/30 shadow-red-500/10',
        ]"
      >
        <!-- 헤더 -->
        <div class="flex items-center justify-between px-3 py-2 border-b border-gray-700/50">
          <div class="flex items-center gap-1.5 min-w-0">
            <Wifi v-if="props.device.isOnline" class="w-3 h-3 text-green-400 flex-shrink-0" />
            <WifiOff v-else class="w-3 h-3 text-red-400 flex-shrink-0" />
            <span class="text-xs sm:text-sm font-semibold text-white truncate">{{ props.device.name }}</span>
          </div>
          <span class="text-[9px] sm:text-[10px] text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded-full flex-shrink-0 ml-1">
            {{ props.device.location }}
          </span>
        </div>

        <!-- 데이터 -->
        <div class="px-3 py-2.5 space-y-2">
          <!-- 전력량 -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <Zap class="w-4 h-4 text-yellow-400" />
              <span class="text-xs text-gray-400">전력</span>
            </div>
            <span v-if="props.device.isOnline"
              :class="[
                'text-sm font-bold',
                (props.device.currentPower * 220) > 500 ? 'text-red-400' : props.device.currentPower > 0 ? 'text-yellow-400' : 'text-gray-500',
              ]"
            >
              {{ (props.device.currentPower * 220).toFixed(1) }}W / {{ props.device.currentPower.toFixed(3) }}A
            </span>
            <span v-else class="text-sm font-bold text-gray-600">--</span>
          </div>

          <!-- 온도 -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <Thermometer class="w-4 h-4 text-orange-400" />
              <span class="text-xs text-gray-400">온도</span>
            </div>
            <span v-if="props.device.isOnline"
              :class="[
                'text-sm font-bold',
                props.device.temperature > 40 ? 'text-red-400' : props.device.temperature > 35 ? 'text-orange-400' : 'text-green-400',
              ]"
            >
              {{ props.device.temperature.toFixed(1) }}°C
            </span>
            <span v-else class="text-sm font-bold text-gray-600">--</span>
          </div>

          <!-- 습도 -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <Droplets class="w-4 h-4 text-sky-400" />
              <span class="text-xs text-gray-400">습도</span>
            </div>
            <span v-if="props.device.isOnline" class="text-sm font-bold text-sky-400">
              {{ props.device.humidity.toFixed(1) }}%
            </span>
            <span v-else class="text-sm font-bold text-gray-600">--</span>
          </div>

          <!-- On/Off 상태 (표시 전용) -->
          <div class="flex items-center justify-between pt-1">
            <div class="flex items-center gap-2">
              <Power class="w-4 h-4 text-blue-400" />
              <span class="text-xs text-gray-400">상태</span>
            </div>
            <span
              :class="[
                'flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium',
                !props.device.isOnline
                  ? 'bg-gray-700 text-gray-500'
                  : props.device.isActive
                    ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                    : 'bg-gray-700/50 text-gray-400 border border-gray-600/30',
              ]"
            >
              <div :class="['w-1.5 h-1.5 rounded-full', props.device.isActive && props.device.isOnline ? 'bg-green-400' : 'bg-gray-500']" />
              {{ !props.device.isOnline ? '오프라인' : props.device.isActive ? 'ON' : 'OFF' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
