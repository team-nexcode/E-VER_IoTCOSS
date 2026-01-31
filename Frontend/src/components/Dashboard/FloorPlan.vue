<script setup lang="ts">
import { ref } from 'vue'
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

// --- 드래그 로직 변수 ---
const svgRef = ref<SVGSVGElement | null>(null)
const isDragging = ref(false)
const draggedDeviceId = ref<number | null>(null)

// 0~100 데이터를 SVG 좌표(900x495)로 변환
function cx(x: number) { return 40 + (x / 100) * 820 }
function cy(y: number) { return 40 + (y / 100) * 415 }

// 마우스 위치를 0~100% 좌표로 역변환
function getPercentFromEvent(e: MouseEvent) {
  if (!svgRef.value) return { x: 0, y: 0 }
  const CTM = svgRef.value.getScreenCTM()
  if (!CTM) return { x: 0, y: 0 }
  
  const pt = svgRef.value.createSVGPoint()
  pt.x = e.clientX
  pt.y = e.clientY
  const svgPt = pt.matrixTransform(CTM.inverse())

  const xPercent = ((svgPt.x - 40) / 820) * 100
  const yPercent = ((svgPt.y - 40) / 415) * 100

  return {
    x: Math.max(0, Math.min(100, xPercent)),
    y: Math.max(0, Math.min(100, yPercent))
  }
}

const startDrag = (deviceId: number) => {
  isDragging.value = true
  draggedDeviceId.value = deviceId
  emit('selectDevice', deviceId) // 드래그 시작 시 선택 효과
}

const onMouseMove = (e: MouseEvent) => {
  if (!isDragging.value || draggedDeviceId.value === null) return
  const { x, y } = getPercentFromEvent(e)
  store.updatePosition(draggedDeviceId.value, x, y)
}

const stopDrag = () => {
  isDragging.value = false
  draggedDeviceId.value = null
}

function getDevice(deviceId: number) {
  return devices.value.find((d) => d.id === deviceId)
}
</script>

<template>
  <div class="h-full flex flex-col bg-gray-900/50 border border-gray-800 rounded-xl p-4 relative overflow-hidden">
    <div class="flex-shrink-0 flex items-center justify-between mb-3">
      <h3 class="text-base font-semibold text-white">실시간 모니터링</h3>
      <div class="flex items-center gap-3 text-[10px]">
        <div class="flex items-center gap-1.5"><div class="w-2 h-2 bg-green-500 rounded-full" /><span class="text-gray-400">활성</span></div>
        <div class="flex items-center gap-1.5"><div class="w-2 h-2 bg-gray-500 rounded-full" /><span class="text-gray-400">비활성</span></div>
        <div class="flex items-center gap-1.5"><div class="w-2 h-2 bg-red-500 rounded-full" /><span class="text-gray-400">오프라인</span></div>
      </div>
    </div>

    <div class="flex-1 min-h-0 relative">
      <svg
        ref="svgRef"
        viewBox="0 0 900 495"
        preserveAspectRatio="xMidYMid meet"
        class="w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
        @mousemove="onMouseMove"
        @mouseup="stopDrag"
        @mouseleave="stopDrag"
      >
        <rect x="0" y="0" width="900" height="495" rx="12" fill="#0c1222" class="cursor-pointer" @click="emit('selectDevice', null)" />

        <rect x="40" y="40" width="820" height="415" rx="4" fill="none" stroke="#334155" stroke-width="3" />
        <line x1="40" y1="250" x2="680" y2="250" stroke="#334155" stroke-width="2" />
        <line x1="380" y1="40" x2="380" y2="455" stroke="#334155" stroke-width="2" />
        <line x1="680" y1="40" x2="680" y2="455" stroke="#334155" stroke-width="2" />

        <g class="select-none pointer-events-none" fill="#475569" font-weight="600" font-size="20">
          <text x="210" y="85" text-anchor="middle">거실</text>
          <text x="530" y="85" text-anchor="middle">주방</text>
          <text x="210" y="300" text-anchor="middle">침실</text>
          <text x="530" y="300" text-anchor="middle">서재</text>
          <text x="790" y="230" text-anchor="middle">욕실</text>
        </g>

        <rect x="70" y="140" width="90" height="35" rx="5" fill="#1e293b" stroke="#334155" />
        <rect x="580" y="55" width="80" height="30" rx="4" fill="#1e293b" stroke="#334155" />
        <rect x="395" y="55" width="40" height="50" rx="4" fill="#1e293b" stroke="#334155" />
        <rect x="70" y="340" width="120" height="80" rx="5" fill="#1e293b" stroke="#334155" />
        <rect x="480" y="370" width="100" height="55" rx="4" fill="#1e293b" stroke="#334155" />
        <rect x="710" y="310" width="110" height="55" rx="8" fill="#1e293b" stroke="#334155" />

        <template v-for="pos in outletPositions" :key="pos.id">
          <g
            v-if="getDevice(pos.deviceId)"
            class="cursor-move"
            @mousedown.prevent="startDrag(pos.deviceId)"
          >
            <circle v-if="highlightedDeviceId === pos.deviceId" :cx="cx(pos.x)" :cy="cy(pos.y)" r="26" fill="none" stroke="#38bdf8" stroke-width="2" opacity="0.6">
              <animate attributeName="r" values="22;30;22" dur="1.5s" repeatCount="indefinite" />
            </circle>

            <circle
              :cx="cx(pos.x)" :cy="cy(pos.y)" r="13"
              :fill="!getDevice(pos.deviceId)!.isOnline ? '#1e293b' : getDevice(pos.deviceId)!.isActive ? '#052e16' : '#1e293b'"
              :stroke="highlightedDeviceId === pos.deviceId ? '#38bdf8' : !getDevice(pos.deviceId)!.isOnline ? '#ef4444' : getDevice(pos.deviceId)!.isActive ? '#22c55e' : '#6b7280'"
              stroke-width="2.5"
            />
            <circle :cx="cx(pos.x)-4" :cy="cy(pos.y)-2" r="2" :fill="getDevice(pos.deviceId)!.isOnline ? (getDevice(pos.deviceId)!.isActive ? '#22c55e' : '#6b7280') : '#ef4444'" />
            <circle :cx="cx(pos.x)+4" :cy="cy(pos.y)-2" r="2" :fill="getDevice(pos.deviceId)!.isOnline ? (getDevice(pos.deviceId)!.isActive ? '#22c55e' : '#6b7280') : '#ef4444'" />

            <text :x="cx(pos.x)" :y="cy(pos.y)+28" text-anchor="middle" :fill="highlightedDeviceId === pos.deviceId ? '#38bdf8' : '#64748b'" font-size="11" class="select-none font-medium">
              {{ getDevice(pos.deviceId)!.name }}
            </text>
          </g>
        </template>
      </svg>
    </div>
  </div>
</template>

<style scoped>
/* 마우스를 올렸을 때 이동 커서로 변경 */
.cursor-move { 
  cursor: move; 
}

/* 드래그할 때 텍스트가 블록 지정(선택)되는 현상 방지 */
.select-none { 
  user-select: none; 
  -webkit-user-select: none;
}
</style>