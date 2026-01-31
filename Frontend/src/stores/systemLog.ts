import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { SystemLog, LogType } from '@/types/systemLog'

const MAX_LOGS = 500

let nextId = 1

export const useSystemLogStore = defineStore('systemLog', () => {
  const mqttStatus = ref<'connected' | 'disconnected' | 'connecting'>('disconnected')
  const mqttBroker = ref('')
  const mqttTopic = ref('')
  const logs = ref<SystemLog[]>([])
  const typeFilter = ref<LogType | ''>('')
  const searchQuery = ref('')
  const totalFromServer = ref(0)
  const serverPage = ref(1)
  const serverSize = 20
  const loadingHistory = ref(false)

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
    // 서버 로그도 삭제
    fetch('/api/system-logs/', { method: 'DELETE' }).catch(() => {})
  }

  async function fetchMqttInfo() {
    try {
      const res = await fetch('/api/health')
      if (res.ok) {
        const data = await res.json()
        if (data.mqtt_broker) mqttBroker.value = data.mqtt_broker
        if (data.mqtt_topic) mqttTopic.value = data.mqtt_topic
        mqttStatus.value = data.mqtt_connected ? 'connected' : 'disconnected'
      }
    } catch {
      // silent
    }
  }

  async function fetchHistoryLogs(page = 1) {
    loadingHistory.value = true
    try {
      const params = new URLSearchParams({
        page: String(page),
        size: String(serverSize),
      })
      if (typeFilter.value) params.set('type', typeFilter.value)
      if (searchQuery.value) params.set('search', searchQuery.value)
      const res = await fetch(`/api/system-logs/?${params}`)
      if (!res.ok) return
      const data = await res.json()
      totalFromServer.value = data.total
      serverPage.value = page

      // 서버 로그를 SystemLog 형식으로 변환
      const serverLogs: SystemLog[] = (data.items || []).map((item: Record<string, unknown>) => {
        const id = nextId++
        return {
          id,
          timestamp: item.timestamp as string,
          type: item.type as LogType,
          level: (item.level as string) || 'info',
          source: (item.source as string) || 'MQTT',
          message: (item.message as string) || '',
          detail: (item.detail as string) || null,
        }
      })
      logs.value = serverLogs
    } catch {
      // silent
    } finally {
      loadingHistory.value = false
    }
  }

  return {
    mqttStatus,
    mqttBroker,
    mqttTopic,
    logs,
    typeFilter,
    searchQuery,
    totalFromServer,
    serverPage,
    serverSize,
    loadingHistory,
    addLog,
    filteredLogs,
    clearLogs,
    fetchMqttInfo,
    fetchHistoryLogs,
  }
})
