<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { BatteryCharging, Clock, Zap, TrendingDown, Banknote, Activity } from 'lucide-vue-next'
import StatusCard from '@/components/Dashboard/StatusCard.vue'
import FloorPlan from '@/components/Dashboard/FloorPlan.vue'
import DevicePanel from '@/components/Dashboard/DevicePanel.vue'
import { useDeviceStore } from '@/stores/device'
import { storeToRefs } from 'pinia'

const selectedDeviceId = ref<number | null>(null)
const store = useDeviceStore()
const { powerSummary, devices } = storeToRefs(store)

let intervalId: number | null = null

onMounted(() => {
  // 초기 로드 시 desired_state 가져오기
  store.fetchDesiredStates()
  
  // 일별 전력량 데이터 로드
  store.fetchDailyPower(7)
  
  // 5초마다 desired_state 동기화
  intervalId = window.setInterval(() => {
    store.fetchDesiredStates()
  }, 5000)
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})

// 디바이스 선택 시 해당 디바이스의 일별 전력량 로드
watch(selectedDeviceId, (newId) => {
  if (newId) {
    const device = devices.value.find(d => d.id === newId)
    if (device) {
      store.fetchDailyPower(7, device.deviceMac)
    }
  } else {
    // 선택 해제 시 전체 데이터 로드
    store.fetchDailyPower(7)
  }
})
</script>

<template>
  <div class="h-[calc(100vh-60px-2rem)] flex flex-col gap-4">
    <!-- 상단: 요약 카드 -->
    <div class="flex-shrink-0 flex items-stretch gap-3 ml-1">
      <div class="flex-1 min-w-0">
        <StatusCard
          title="이번달 누적 전력량"
          :value="powerSummary.monthlyEnergy.toFixed(3)"
          unit="kWh"
          color="blue"
        >
          <template #icon>
            <BatteryCharging class="w-5 h-5" />
          </template>
        </StatusCard>
      </div>
      <div class="flex-1 min-w-0">
        <StatusCard
          title="어제 전력량"
          :value="powerSummary.yesterdayEnergy.toFixed(3)"
          unit="kWh"
          color="yellow"
        >
          <template #icon>
            <Clock class="w-5 h-5" />
          </template>
        </StatusCard>
      </div>
      <div class="flex-1 min-w-0">
        <StatusCard
          title="오늘 전력량"
          :value="powerSummary.todayEnergy.toFixed(3)"
          unit="kWh"
          color="green"
          :trend="{ value: -12.5, isPositive: true }"
        >
          <template #icon>
            <Zap class="w-5 h-5" />
          </template>
        </StatusCard>
      </div>
      <div class="flex-1 min-w-0">
        <StatusCard
          title="예상 절감률"
          :value="powerSummary.savingsPercent.toFixed(1)"
          unit="%"
          color="green"
          :trend="{ value: 3.2, isPositive: true }"
        >
          <template #icon>
            <TrendingDown class="w-5 h-5" />
          </template>
        </StatusCard>
      </div>

      <!-- 구분선 -->
      <div class="w-px bg-gray-700/50 self-stretch my-2 flex-shrink-0" />

      <div class="flex-1 min-w-0">
        <StatusCard
          title="예상 전기요금"
          :value="powerSummary.estimatedCost.toLocaleString()"
          unit="원"
          color="purple"
        >
          <template #icon>
            <Banknote class="w-5 h-5" />
          </template>
        </StatusCard>
      </div>
      <div class="flex-1 min-w-0">
        <StatusCard
          title="실시간 소비전력"
          :value="powerSummary.peakPower.toLocaleString()"
          unit="W"
          color="red"
        >
          <template #icon>
            <Activity class="w-5 h-5" />
          </template>
        </StatusCard>
      </div>
    </div>

    <!-- 하단: 구조도(좌) + 디바이스 패널(우) -->
    <div class="flex-1 min-h-0 flex gap-4">
      <div class="flex-1 min-w-0">
        <FloorPlan
          :highlighted-device-id="selectedDeviceId"
          @select-device="selectedDeviceId = $event"
        />
      </div>
      <div class="w-80 flex-shrink-0">
        <DevicePanel
          :selected-device-id="selectedDeviceId"
          @select-device="selectedDeviceId = $event"
        />
      </div>
    </div>
  </div>
</template>
