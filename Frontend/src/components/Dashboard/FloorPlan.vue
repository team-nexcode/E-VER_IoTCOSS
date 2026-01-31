<script setup lang="ts">
import { useDeviceStore } from '@/stores/device'
import { storeToRefs } from 'pinia'

defineProps<{
  highlightedDeviceId: number | null
}>()

const emit = defineEmits<{
  selectDevice: [id: number | null]
}>()

const store = useDeviceStore()
const { devices, outletPositions } = storeToRefs(store)

function getDevice(deviceId: number) {
  return devices.value.find((d) => d.id === deviceId)
}

function cx(x: number) {
  return 40 + (x / 100) * 820
}

function cy(y: number) {
  return 40 + (y / 100) * 415
}
</script>

<template>
  <div class="h-full flex flex-col bg-gray-900/50 border border-gray-800 rounded-xl p-4 relative overflow-hidden">
    <!-- 헤더 -->
    <div class="flex-shrink-0 flex items-center justify-between mb-3">
      <h3 class="text-base font-semibold text-white">실시간 모니터링</h3>
      <div class="flex items-center gap-3 text-[10px]">
        <div class="flex items-center gap-1.5">
          <div class="w-2 h-2 bg-green-500 rounded-full" />
          <span class="text-gray-400">활성</span>
        </div>
        <div class="flex items-center gap-1.5">
          <div class="w-2 h-2 bg-gray-500 rounded-full" />
          <span class="text-gray-400">비활성</span>
        </div>
        <div class="flex items-center gap-1.5">
          <div class="w-2 h-2 bg-red-500 rounded-full" />
          <span class="text-gray-400">오프라인</span>
        </div>
      </div>
    </div>

    <!-- 구조도 SVG -->
    <div class="flex-1 min-h-0 relative">
      <svg
        viewBox="0 0 900 495"
        preserveAspectRatio="xMidYMid meet"
        class="w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
      >
        <!-- 배경 (클릭시 선택 해제) -->
        <rect
          x="0" y="0" width="900" height="495" rx="12" fill="#0c1222"
          class="cursor-pointer" @click="emit('selectDevice', null)"
        />

        <!-- 외벽 -->
        <rect
          x="40" y="40" width="820" height="415" rx="4"
          fill="none" stroke="#334155" stroke-width="3"
        />

        <!-- 방 구분선 -->
        <line x1="40" y1="250" x2="680" y2="250" stroke="#334155" stroke-width="2" />
        <line x1="380" y1="40" x2="380" y2="455" stroke="#334155" stroke-width="2" />
        <line x1="680" y1="40" x2="680" y2="455" stroke="#334155" stroke-width="2" />

        <!-- 방 이름 -->
        <text x="210" y="85" text-anchor="middle" fill="#475569" font-size="20" font-weight="600">거실</text>
        <text x="210" y="107" text-anchor="middle" fill="#334155" font-size="11">Living Room</text>
        <text x="530" y="85" text-anchor="middle" fill="#475569" font-size="20" font-weight="600">주방</text>
        <text x="530" y="107" text-anchor="middle" fill="#334155" font-size="11">Kitchen</text>
        <text x="210" y="300" text-anchor="middle" fill="#475569" font-size="20" font-weight="600">침실</text>
        <text x="210" y="322" text-anchor="middle" fill="#334155" font-size="11">Bedroom</text>
        <text x="530" y="300" text-anchor="middle" fill="#475569" font-size="20" font-weight="600">서재</text>
        <text x="530" y="322" text-anchor="middle" fill="#334155" font-size="11">Study</text>
        <text x="790" y="230" text-anchor="middle" fill="#475569" font-size="20" font-weight="600">욕실</text>
        <text x="790" y="252" text-anchor="middle" fill="#334155" font-size="11">Bathroom</text>

        <!-- 문 -->
        <rect x="370" y="125" width="20" height="45" fill="#0c1222" />
        <line x1="370" y1="125" x2="370" y2="170" stroke="#60a5fa" stroke-width="2" stroke-dasharray="4" />
        <line x1="390" y1="125" x2="390" y2="170" stroke="#60a5fa" stroke-width="2" stroke-dasharray="4" />
        <rect x="370" y="330" width="20" height="45" fill="#0c1222" />
        <line x1="370" y1="330" x2="370" y2="375" stroke="#60a5fa" stroke-width="2" stroke-dasharray="4" />
        <line x1="390" y1="330" x2="390" y2="375" stroke="#60a5fa" stroke-width="2" stroke-dasharray="4" />
        <rect x="150" y="240" width="50" height="20" fill="#0c1222" />
        <line x1="150" y1="240" x2="200" y2="240" stroke="#60a5fa" stroke-width="2" stroke-dasharray="4" />
        <line x1="150" y1="260" x2="200" y2="260" stroke="#60a5fa" stroke-width="2" stroke-dasharray="4" />
        <rect x="670" y="130" width="20" height="45" fill="#0c1222" />
        <line x1="670" y1="130" x2="670" y2="175" stroke="#60a5fa" stroke-width="2" stroke-dasharray="4" />
        <line x1="690" y1="130" x2="690" y2="175" stroke="#60a5fa" stroke-width="2" stroke-dasharray="4" />
        <rect x="300" y="445" width="70" height="20" fill="#0c1222" />
        <line x1="300" y1="455" x2="370" y2="455" stroke="#f59e0b" stroke-width="2.5" />
        <text x="335" y="483" text-anchor="middle" fill="#f59e0b" font-size="11" font-weight="500">현관</text>

        <!-- 가구 -->
        <rect x="70" y="140" width="90" height="35" rx="5" fill="#1e293b" stroke="#334155" stroke-width="1" />
        <text x="115" y="163" text-anchor="middle" fill="#334155" font-size="10">소파</text>
        <rect x="280" y="140" width="8" height="50" rx="2" fill="#1e293b" stroke="#334155" stroke-width="1" />
        <rect x="580" y="55" width="80" height="30" rx="4" fill="#1e293b" stroke="#334155" stroke-width="1" />
        <text x="620" y="75" text-anchor="middle" fill="#334155" font-size="10">싱크대</text>
        <rect x="395" y="55" width="40" height="50" rx="4" fill="#1e293b" stroke="#334155" stroke-width="1" />
        <text x="415" y="84" text-anchor="middle" fill="#334155" font-size="9">냉장고</text>
        <rect x="70" y="340" width="120" height="80" rx="5" fill="#1e293b" stroke="#334155" stroke-width="1" />
        <text x="130" y="385" text-anchor="middle" fill="#334155" font-size="10">침대</text>
        <rect x="480" y="370" width="100" height="55" rx="4" fill="#1e293b" stroke="#334155" stroke-width="1" />
        <text x="530" y="402" text-anchor="middle" fill="#334155" font-size="10">책상</text>
        <rect x="710" y="310" width="110" height="55" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1" />
        <text x="765" y="342" text-anchor="middle" fill="#334155" font-size="10">욕조</text>
        <circle cx="740" cy="90" r="20" fill="#1e293b" stroke="#334155" stroke-width="1" />
        <text x="740" y="94" text-anchor="middle" fill="#334155" font-size="9">세면대</text>

        <!-- 콘센트 마커 -->
        <template v-for="pos in outletPositions" :key="pos.id">
          <g
            v-if="getDevice(pos.deviceId)"
            class="cursor-pointer"
            @click="emit('selectDevice', highlightedDeviceId === pos.deviceId ? null : pos.deviceId)"
          >
            <!-- 선택 하이라이트 링 -->
            <template v-if="highlightedDeviceId === pos.deviceId">
              <circle :cx="cx(pos.x)" :cy="cy(pos.y)" r="26" fill="none" stroke="#38bdf8" stroke-width="2" opacity="0.6">
                <animate attributeName="r" values="22;30;22" dur="1.5s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.7;0.2;0.7" dur="1.5s" repeatCount="indefinite" />
              </circle>
              <circle :cx="cx(pos.x)" :cy="cy(pos.y)" r="20" fill="#38bdf8" opacity="0.1" />
            </template>

            <!-- 활성 디바이스 글로우 -->
            <circle
              v-if="getDevice(pos.deviceId)!.isActive && getDevice(pos.deviceId)!.isOnline && highlightedDeviceId !== pos.deviceId"
              :cx="cx(pos.x)" :cy="cy(pos.y)" r="18" fill="none" stroke="#22c55e" stroke-width="1" opacity="0.3"
            >
              <animate attributeName="r" values="14;24;14" dur="2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.4;0.1;0.4" dur="2s" repeatCount="indefinite" />
            </circle>

            <!-- 고전력 경고 -->
            <circle
              v-if="getDevice(pos.deviceId)!.currentPower > 1000 && getDevice(pos.deviceId)!.isOnline && highlightedDeviceId !== pos.deviceId"
              :cx="cx(pos.x)" :cy="cy(pos.y)" r="18" fill="none" stroke="#ef4444" stroke-width="1.5" opacity="0.4"
            >
              <animate attributeName="r" values="16;26;16" dur="1.5s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.5;0.1;0.5" dur="1.5s" repeatCount="indefinite" />
            </circle>

            <!-- 콘센트 외부 원 -->
            <circle
              :cx="cx(pos.x)" :cy="cy(pos.y)" r="13"
              :fill="!getDevice(pos.deviceId)!.isOnline ? '#1e293b' : getDevice(pos.deviceId)!.isActive ? '#052e16' : '#1e293b'"
              :stroke="highlightedDeviceId === pos.deviceId ? '#38bdf8' : !getDevice(pos.deviceId)!.isOnline ? '#ef4444' : getDevice(pos.deviceId)!.isActive ? '#22c55e' : '#6b7280'"
              :stroke-width="highlightedDeviceId === pos.deviceId ? '3' : '2.5'"
            />

            <!-- 콘센트 구멍 -->
            <circle
              :cx="cx(pos.x) - 4" :cy="cy(pos.y) - 2" r="2"
              :fill="!getDevice(pos.deviceId)!.isOnline ? '#ef4444' : getDevice(pos.deviceId)!.isActive ? '#22c55e' : '#6b7280'"
            />
            <circle
              :cx="cx(pos.x) + 4" :cy="cy(pos.y) - 2" r="2"
              :fill="!getDevice(pos.deviceId)!.isOnline ? '#ef4444' : getDevice(pos.deviceId)!.isActive ? '#22c55e' : '#6b7280'"
            />
            <rect
              :x="cx(pos.x) - 2.5" :y="cy(pos.y) + 2" width="5" height="2.5" rx="1"
              :fill="!getDevice(pos.deviceId)!.isOnline ? '#ef4444' : getDevice(pos.deviceId)!.isActive ? '#22c55e' : '#6b7280'"
            />

            <!-- 디바이스 이름 라벨 -->
            <text
              :x="cx(pos.x)" :y="cy(pos.y) + 28"
              text-anchor="middle"
              :fill="highlightedDeviceId === pos.deviceId ? '#38bdf8' : '#64748b'"
              font-size="11"
              :font-weight="highlightedDeviceId === pos.deviceId ? '600' : '400'"
            >
              {{ getDevice(pos.deviceId)!.name }}
            </text>
          </g>
        </template>
      </svg>
    </div>
  </div>
</template>
