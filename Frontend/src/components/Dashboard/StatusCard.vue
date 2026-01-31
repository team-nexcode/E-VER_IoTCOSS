<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  unit?: string
  trend?: { value: number; isPositive: boolean }
  color: 'blue' | 'green' | 'yellow' | 'red' | 'purple'
}>()

const colorMap: Record<string, string> = {
  blue: 'from-blue-600/20 to-blue-600/5 border-blue-500/20',
  green: 'from-green-600/20 to-green-600/5 border-green-500/20',
  yellow: 'from-yellow-600/20 to-yellow-600/5 border-yellow-500/20',
  red: 'from-red-600/20 to-red-600/5 border-red-500/20',
  purple: 'from-purple-600/20 to-purple-600/5 border-purple-500/20',
}

const iconBgMap: Record<string, string> = {
  blue: 'bg-blue-600/20 text-blue-400',
  green: 'bg-green-600/20 text-green-400',
  yellow: 'bg-yellow-600/20 text-yellow-400',
  red: 'bg-red-600/20 text-red-400',
  purple: 'bg-purple-600/20 text-purple-400',
}
</script>

<template>
  <div
    :class="['bg-gradient-to-br border rounded-xl p-4 transition-transform hover:scale-[1.02] min-w-0 h-28 flex flex-col', colorMap[color]]"
    style="padding: 16px"
  >
    <div class="flex items-start justify-between mb-2">
      <span class="text-xs sm:text-sm text-gray-400 truncate">{{ title }}</span>
      <div :class="['w-8 h-8 sm:w-9 sm:h-9 rounded-lg flex-shrink-0 flex items-center justify-center', iconBgMap[color]]">
        <slot name="icon" />
      </div>
    </div>
    <div class="flex items-end gap-1.5">
      <span class="text-lg sm:text-xl font-bold text-white truncate">{{ value }}</span>
      <span v-if="unit" class="text-[10px] sm:text-xs text-gray-500 mb-0.5 flex-shrink-0">{{ unit }}</span>
    </div>
    <div class="mt-auto h-4 flex items-center gap-1">
      <template v-if="trend">
        <span
          :class="['text-[10px] sm:text-xs font-medium', trend.isPositive ? 'text-green-400' : 'text-red-400']"
        >
          {{ trend.isPositive ? '+' : '' }}{{ trend.value }}%
        </span>
        <span class="text-[10px] sm:text-xs text-gray-600">전일 대비</span>
      </template>
    </div>
  </div>
</template>
