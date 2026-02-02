<script setup lang="ts">
import { ref, onMounted, onUnmounted, type Component, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  LayoutDashboard,
  Plug,
  BarChart3,
  Clock,
  Bell,
  Monitor,
  Bot,
  ChevronDown,
  ChevronUp
} from 'lucide-vue-next'
import { useDeviceStore } from '@/stores/device' // 프로젝트에 따라 useDeviceMacStore로 변경 가능
import { storeToRefs } from 'pinia'

const route = useRoute()
const deviceStore = useDeviceStore()
const { devices } = storeToRefs(deviceStore)

/** =========================
 * Nav Items
 * ========================= */
const navItems = [
  { to: '/', icon: LayoutDashboard, label: '대시보드' },
  { to: '/devices', icon: Plug, label: '디바이스' },
  { to: '/power', icon: BarChart3, label: '전력 분석' },
  { to: '/schedule', icon: Clock, label: '스케줄' },
  { to: '/alerts', icon: Bell, label: '알림' },
  { to: '/system-log', icon: Monitor, label: 'System Log' },
]

/** =========================
 * AI 디바이스별 토글 로직
 * ========================= */
const isAIPanelOpen = ref(false)
const aiSettings = ref<Record<number, boolean>>({})

onMounted(() => {
  const saved = localStorage.getItem('ai_device_settings')
  if (saved) aiSettings.value = JSON.parse(saved)
})

watch(aiSettings, (newVal) => {
  localStorage.setItem('ai_device_settings', JSON.stringify(newVal))
}, { deep: true })

const isAllSelected = computed(() => {
  if (devices.value.length === 0) return false
  return devices.value.every(d => aiSettings.value[d.id])
})

function toggleAllAI() {
  const targetState = !isAllSelected.value
  const newSettings = { ...aiSettings.value }
  devices.value.forEach(d => { newSettings[d.id] = targetState })
  aiSettings.value = newSettings
}

/** =========================
 * 🕒 Clock & Server Sync (복구 완료!)
 * ========================= */
const responseTime = ref<number | null>(null)
const status = ref<'checking' | 'online' | 'offline'>('checking')
const displayTime = ref('--:--:--')
const displayDate = ref('')
const serverOffset = ref<number | null>(null)

let syncInterval: any = null
let clockInterval: any = null

async function syncTime() {
  const start = performance.now()
  try {
    const res = await fetch('/api/health')
    const elapsed = performance.now() - start
    if (res.ok) {
      const data = await res.json()
      responseTime.value = Math.round(elapsed)
      status.value = 'online'
      const serverMs = new Date(data.server_time).getTime()
      serverOffset.value = serverMs - Date.now()
    } else {
      status.value = 'offline'
    }
  } catch {
    status.value = 'offline'
  }
}

function tick() {
  if (serverOffset.value === null) return
  const now = new Date(Date.now() + serverOffset.value)
  displayTime.value = now.toLocaleTimeString('ko-KR', { hour12: true, timeZone: 'Asia/Seoul' })
  displayDate.value = now.toLocaleDateString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short', timeZone: 'Asia/Seoul',
  })
}

function isActive(to: string) {
  return to === '/' ? route.path === '/' : route.path.startsWith(to)
}

onMounted(() => {
  syncTime()
  syncInterval = setInterval(syncTime, 10000)
  clockInterval = setInterval(tick, 1000)
})

onUnmounted(() => {
  clearInterval(syncInterval)
  clearInterval(clockInterval)
})
</script>

<template>
  <aside
    class="fixed left-0 bottom-0 w-[240px] bg-[#111827] border-r border-gray-800 flex flex-col z-40 shadow-2xl"
    :style="{ top: 'var(--topbar-height, 60px)' }"
  >
    <nav class="flex-1 px-4 overflow-y-auto custom-scroll">
      <div class="w-full space-y-2 py-6">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="[
            'group relative flex items-center gap-5 px-5 py-4 rounded-3xl text-lg font-bold transition-all border',
            isActive(item.to) ? 'bg-white/[0.06] text-white border-white/10 shadow-lg' : 'text-gray-400 border-transparent hover:text-white hover:bg-white/[0.02]'
          ]"
        >
          <component :is="item.icon" :class="['w-6 h-6', isActive(item.to) ? 'text-blue-400' : 'text-gray-400']" />
          <span class="flex-1 truncate">{{ item.label }}</span>
        </RouterLink>
      </div>
    </nav>

    <div class="px-4 pb-4">
      <div class="h-px bg-gradient-to-r from-transparent via-gray-700/60 to-transparent mb-4" />
      
      <div class="bg-blue-500/5 border border-blue-500/10 rounded overflow-hidden">
        <button @click="isAIPanelOpen = !isAIPanelOpen" class="w-full flex items-center justify-between p-5 hover:bg-blue-500/10 transition-colors">
          <div class="flex items-center gap-3">
            <div class="p-2.5 bg-blue-500/15 rounded-xl text-blue-400"><Bot class="w-6 h-6" /></div>
            <div class="text-left">
              <p class="text-[17px] font-bold text-white leading-none">AI 자동 차단</p>
              <p class="text-[12px] text-blue-400/60 mt-1.5 uppercase font-bold tracking-widest">Device Select</p>
            </div>
          </div>
          <component :is="isAIPanelOpen ? ChevronUp : ChevronDown" class="w-4 h-4 text-gray-500" />
        </button>

        <div v-if="isAIPanelOpen" class="px-5 pb-5 space-y-4 max-h-[180px] overflow-y-auto custom-scroll border-t border-white/5 pt-4">
          <div class="flex items-center justify-between pb-2 border-b border-white/5">
            <span class="text-[13px] font-bold text-blue-400 uppercase">전체 적용</span>
            <button @click="toggleAllAI" :class="['relative inline-flex h-5 w-10 items-center rounded-full transition-colors', isAllSelected ? 'bg-blue-600' : 'bg-gray-700']">
              <span :class="['inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform', isAllSelected ? 'translate-x-5' : 'translate-x-1']" />
            </button>
          </div>
          <div v-for="device in devices" :key="device.id" class="flex items-center justify-between">
            <div class="flex flex-col min-w-0">
              <span class="text-sm font-bold text-gray-300 truncate">{{ device.name }}</span>
              <span class="text-[11px] text-gray-500 uppercase">{{ device.location }}</span>
            </div>
            <button @click="aiSettings[device.id] = !aiSettings[device.id]" :class="['relative inline-flex h-4.5 w-8 items-center rounded-full transition-colors', aiSettings[device.id] ? 'bg-blue-500' : 'bg-gray-800']">
              <span :class="['inline-block h-3 w-3 transform rounded-full bg-white transition-transform', aiSettings[device.id] ? 'translate-x-4' : 'translate-x-0.5']" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="p-6 border-t border-gray-800 space-y-4 bg-[#0d121f]">
      <div class="bg-white/[0.03] border border-white/10 rounded-2xl p-4 text-center shadow-inner">
        <template v-if="status === 'offline'">
          <p class="text-sm font-mono font-bold text-red-400 uppercase">OFFLINE</p>
        </template>
        <template v-else>
          <p class="text-2xl font-mono font-bold text-white tracking-wider leading-none">{{ displayTime }}</p>
          <p class="text-[11px] text-gray-500 mt-2 font-medium">{{ displayDate }}</p>
        </template>
      </div>

      <div class="flex items-center justify-between px-1">
        <div class="flex items-center gap-2">
          <div :class="['w-2 h-2 rounded-full shadow-[0_0_8px]', status === 'online' ? 'bg-green-500 shadow-green-500 animate-pulse' : 'bg-red-500 shadow-red-500']" />
          <span class="text-[11px] font-bold text-gray-500 uppercase tracking-widest">System</span>
        </div>
        <span class="text-[10px] font-mono text-gray-600 font-bold uppercase">
          {{ status === 'online' ? (responseTime ? `${responseTime}ms` : 'Active') : 'Error' }}
        </span>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.custom-scroll::-webkit-scrollbar { width: 4px; }
.custom-scroll::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
nav { -ms-overflow-style: none; scrollbar-width: none; }
nav::-webkit-scrollbar { display: none; }
</style>