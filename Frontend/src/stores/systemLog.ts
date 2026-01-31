import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { SystemLog, LogType } from '@/types/systemLog'

const MAX_LOGS = 500

let nextId = 1

export const useSystemLogStore = defineStore('systemLog', () => {
  const mqttStatus = ref<'connected' | 'disconnected' | 'connecting'>('disconnected')
  const logs = ref<SystemLog[]>([])
  const typeFilter = ref<LogType | ''>('')
  const searchQuery = ref('')

  function addLog(log: Omit<SystemLog, 'id' | 'timestamp'>) {
    const entry: SystemLog = {
      id: nextId++,
      timestamp: new Date().toISOString(),
      ...log,
    }
    logs.value.unshift(entry)
    if (logs.value.length > MAX_LOGS) {
      logs.value = logs.value.slice(0, MAX_LOGS)
    }
  }

  const filteredLogs = computed(() => {
    let result = logs.value
    if (typeFilter.value) {
      result = result.filter((l) => l.type === typeFilter.value)
    }
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      result = result.filter(
        (l) =>
          l.message.toLowerCase().includes(q) ||
          l.source.toLowerCase().includes(q) ||
          (l.detail && l.detail.toLowerCase().includes(q)),
      )
    }
    return result
  })

  function clearLogs() {
    logs.value = []
  }

  return {
    mqttStatus,
    logs,
    typeFilter,
    searchQuery,
    addLog,
    filteredLogs,
    clearLogs,
  }
})
