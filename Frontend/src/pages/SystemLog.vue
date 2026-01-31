<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Monitor, ChevronDown, ChevronRight, Trash2, Search } from 'lucide-vue-next'
import { useSystemLogStore } from '@/stores/systemLog'
import type { LogType } from '@/types/systemLog'

const store = useSystemLogStore()

const page = ref(1)
const size = 20
const expandedId = ref<number | null>(null)

const TYPE_BADGES: Record<LogType, string> = {
  CONNECTION: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  MESSAGE: 'bg-green-500/20 text-green-400 border-green-500/30',
  ERROR: 'bg-red-500/20 text-red-400 border-red-500/30',
  SYSTEM: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
}

const LEVEL_COLORS: Record<string, string> = {
  info: 'text-blue-400',
  warn: 'text-yellow-400',
  error: 'text-red-400',
}

const MQTT_STATUS_STYLE: Record<string, { dot: string; text: string; label: string }> = {
  connected: { dot: 'bg-green-500', text: 'text-green-400', label: 'Connected' },
  disconnected: { dot: 'bg-red-500', text: 'text-red-400', label: 'Disconnected' },
  connecting: { dot: 'bg-yellow-500 animate-pulse', text: 'text-yellow-400', label: 'Connecting...' },
}

const typeOptions: { value: LogType | ''; label: string }[] = [
  { value: '', label: 'All' },
  { value: 'CONNECTION', label: 'Connection' },
  { value: 'MESSAGE', label: 'Message' },
  { value: 'ERROR', label: 'Error' },
  { value: 'SYSTEM', label: 'System' },
]

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

function formatJson(raw: string | null): string {
  if (!raw) return '-'
  try {
    return JSON.stringify(JSON.parse(raw), null, 2)
  } catch {
    return raw
  }
}

// Paginated view of filtered logs
const paginatedLogs = computed(() => {
  const start = (page.value - 1) * size
  return store.filteredLogs.slice(start, start + size)
})

const totalFiltered = computed(() => store.filteredLogs.length)
const totalPages = computed(() => Math.ceil(totalFiltered.value / size))

function handleClear() {
  if (!confirm('모든 시스템 로그를 삭제하시겠습니까?')) return
  store.clearLogs()
  page.value = 1
}

function setTypeFilter(val: LogType | '') {
  store.typeFilter = val
  page.value = 1
}

function setSearch(val: string) {
  store.searchQuery = val
  page.value = 1
}

const mqttStyle = computed(() => MQTT_STATUS_STYLE[store.mqttStatus])

onMounted(() => {
  store.fetchMqttInfo()
})
</script>

<template>
  <div class="space-y-6">
    <!-- 헤더 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-white">System Log</h2>
        <p class="text-sm text-gray-500 mt-1">MQTT 연결 및 시스템 로그를 확인하세요</p>
      </div>

      <!-- MQTT 상태 인디케이터 -->
      <div class="flex items-center gap-3 bg-gray-900/50 border border-gray-800 rounded-xl px-4 py-2.5">
        <span v-if="store.mqttBroker" class="text-xs font-mono text-gray-500">
          {{ store.mqttBroker }}
        </span>
        <div class="flex items-center gap-2">
          <div :class="['w-2.5 h-2.5 rounded-full', mqttStyle.dot]" />
          <span class="text-xs font-medium text-gray-400">MQTT</span>
        </div>
        <span :class="['text-sm font-semibold', mqttStyle.text]">
          {{ mqttStyle.label }}
        </span>
      </div>
    </div>

    <!-- 필터 바 -->
    <div class="flex flex-wrap items-center gap-3 bg-gray-900/50 border border-gray-800 rounded-2xl p-4">
      <!-- 타입 필터 -->
      <select
        :value="store.typeFilter"
        class="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500"
        @change="setTypeFilter(($event.target as HTMLSelectElement).value as LogType | '')"
      >
        <option v-for="opt in typeOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <!-- 검색 -->
      <div class="relative flex-1 min-w-[200px]">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          type="text"
          placeholder="메시지 검색..."
          :value="store.searchQuery"
          class="w-full bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:border-blue-500"
          @input="setSearch(($event.target as HTMLInputElement).value)"
        />
      </div>

      <!-- 전체 삭제 -->
      <button
        class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm bg-red-600/10 text-red-400 border border-red-500/20 hover:bg-red-600/20 transition-colors"
        @click="handleClear"
      >
        <Trash2 class="w-4 h-4" />
        전체 삭제
      </button>
    </div>

    <!-- 로그 테이블 -->
    <div class="bg-gray-900/50 border border-gray-800 rounded-2xl overflow-hidden">
      <!-- 테이블 헤더 -->
      <div class="grid grid-cols-[40px_90px_140px_60px_70px_1fr] gap-2 px-4 py-3 text-xs font-medium text-gray-500 uppercase border-b border-gray-800">
        <span />
        <span>타입</span>
        <span>시각</span>
        <span>레벨</span>
        <span>소스</span>
        <span>메시지</span>
      </div>

      <!-- 빈 상태 -->
      <div v-if="store.filteredLogs.length === 0" class="flex flex-col items-center justify-center h-32 text-gray-500">
        <Monitor class="w-8 h-8 mb-2 text-gray-600" />
        <span>기록된 시스템 로그가 없습니다</span>
      </div>

      <!-- 로그 행 -->
      <template v-else>
        <div v-for="log in paginatedLogs" :key="log.id">
          <!-- 요약 행 -->
          <div
            class="grid grid-cols-[40px_90px_140px_60px_70px_1fr] gap-2 px-4 py-3 text-sm cursor-pointer hover:bg-gray-800/50 border-b border-gray-800/50 transition-colors"
            @click="expandedId = expandedId === log.id ? null : log.id"
          >
            <span class="flex items-center text-gray-600">
              <ChevronDown v-if="expandedId === log.id" class="w-4 h-4" />
              <ChevronRight v-else class="w-4 h-4" />
            </span>

            <!-- 타입 뱃지 -->
            <span>
              <span
                :class="[
                  'inline-block px-2 py-0.5 text-[10px] font-semibold rounded border',
                  TYPE_BADGES[log.type],
                ]"
              >
                {{ log.type }}
              </span>
            </span>

            <!-- 시각 -->
            <span class="text-gray-400 font-mono text-xs">
              {{ formatTime(log.timestamp) }}
            </span>

            <!-- 레벨 -->
            <span :class="['text-xs font-medium uppercase', LEVEL_COLORS[log.level] || 'text-gray-400']">
              {{ log.level }}
            </span>

            <!-- 소스 -->
            <span class="text-gray-400 text-xs">
              {{ log.source }}
            </span>

            <!-- 메시지 -->
            <span class="text-gray-300 truncate text-xs" :title="log.message">
              {{ log.message }}
            </span>
          </div>

          <!-- 상세 확장 -->
          <div v-if="expandedId === log.id" class="px-6 py-4 bg-gray-800/30 border-b border-gray-800 space-y-3">
            <div>
              <h4 class="text-xs font-semibold text-gray-400 uppercase mb-2">Detail</h4>
              <pre
                v-if="log.detail"
                class="bg-gray-900 rounded-lg p-3 text-xs text-gray-300 overflow-auto max-h-64 font-mono"
              >{{ formatJson(log.detail) }}</pre>
              <p v-else class="text-xs text-gray-500">상세 정보 없음</p>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- 페이지네이션 -->
    <div v-if="totalPages > 1" class="flex items-center justify-between text-sm">
      <span class="text-gray-500">
        총 {{ totalFiltered }}건 중 {{ (page - 1) * size + 1 }}–{{ Math.min(page * size, totalFiltered) }}건
      </span>
      <div class="flex items-center gap-2">
        <button
          :disabled="page <= 1"
          class="px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 border border-gray-700 disabled:opacity-40 hover:text-white transition-colors"
          @click="page = Math.max(1, page - 1)"
        >
          이전
        </button>
        <span class="text-gray-400">
          {{ page }} / {{ totalPages }}
        </span>
        <button
          :disabled="page >= totalPages"
          class="px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 border border-gray-700 disabled:opacity-40 hover:text-white transition-colors"
          @click="page = Math.min(totalPages, page + 1)"
        >
          다음
        </button>
      </div>
    </div>
  </div>
</template>
