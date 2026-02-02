<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { useDeviceStore } from '@/stores/device'
import { storeToRefs } from 'pinia'

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  selectedDeviceId: number | null
}>()

const store = useDeviceStore()
const { devices, dailyPowerTotal, dailyPowerByDevice } = storeToRefs(store)

const selectedDevice = computed(() =>
  props.selectedDeviceId ? devices.value.find((d) => d.id === props.selectedDeviceId) : null
)

const data = computed(() =>
  props.selectedDeviceId
    ? (dailyPowerByDevice.value[props.selectedDeviceId] ?? dailyPowerTotal.value)
    : dailyPowerTotal.value
)

const barColor = computed(() => (props.selectedDeviceId ? '#38bdf8' : '#3b82f6'))

const title = computed(() =>
  selectedDevice.value ? `${selectedDevice.value.name} - 일별 전력량` : '일별 총 전력량'
)

// 전체 사용량의 최댓값으로 y축 고정 (모든 그래프에서 동일한 스케일 사용)
const maxPowerValue = computed(() => {
  return Math.max(...dailyPowerTotal.value.map(d => d.power), 0)
})

const chartOption = computed(() => ({
  grid: {
    top: 8,
    right: 8,
    bottom: 0,
    left: 0,
    containLabel: true,
  },
  tooltip: {
    trigger: 'axis' as const,
    backgroundColor: '#1e293b',
    borderColor: '#334155',
    borderWidth: 1,
    textStyle: { color: '#e2e8f0', fontSize: 12 },
    formatter: (params: Array<{ name: string; value: number }>) => {
      const item = params[0]
      return `${item.name}<br/>전력량: ${item.value} kWh`
    },
  },
  xAxis: {
    type: 'category' as const,
    data: data.value.map((d) => d.date),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#64748b', fontSize: 10 },
  },
  yAxis: {
    type: 'value' as const,
    max: maxPowerValue.value > 0 ? Math.ceil(maxPowerValue.value * 1.1) : undefined,  // 최대값의 110%로 고정
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#64748b', fontSize: 10 },
    splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' as const } },
  },
  series: [
    {
      type: 'bar' as const,
      data: data.value.map((d) => d.power),
      itemStyle: {
        color: barColor.value,
        borderRadius: [3, 3, 0, 0],
      },
      barMaxWidth: 28,
    },
  ],
}))
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="flex-shrink-0 px-3 pt-3 pb-1">
      <span class="text-[11px] font-medium text-gray-400">{{ title }}</span>
    </div>
    <div class="flex-1 min-h-0">
      <VChart :option="chartOption" autoresize class="w-full h-full" />
    </div>
  </div>
</template>
