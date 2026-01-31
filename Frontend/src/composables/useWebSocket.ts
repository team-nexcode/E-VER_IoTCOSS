import { ref, onUnmounted } from 'vue'
import { useDeviceStore } from '@/stores/device'
import { useSystemLogStore } from '@/stores/systemLog'
import type { Device } from '@/types/device'

export function useWebSocket(url: string) {
  const isConnected = ref(false)
  const error = ref<string | null>(null)
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  const RECONNECT_DELAY = 3000

  const store = useDeviceStore()
  const logStore = useSystemLogStore()

  function connect() {
    if (ws) {
      ws.close()
    }

    logStore.mqttStatus = 'connecting'
    logStore.addLog({
      type: 'CONNECTION',
      level: 'info',
      source: 'MQTT',
      message: `연결 시도: ${url}`,
      detail: JSON.stringify({ url, timestamp: new Date().toISOString() }),
    })

    ws = new WebSocket(url)

    ws.onopen = () => {
      isConnected.value = true
      error.value = null
      logStore.mqttStatus = 'connected'
      logStore.addLog({
        type: 'CONNECTION',
        level: 'info',
        source: 'MQTT',
        message: '연결 성공',
        detail: JSON.stringify({ url, timestamp: new Date().toISOString() }),
      })
    }

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as Partial<Device> & { id: number }
        const devices = store.devices.map((d) =>
          d.id === data.id ? { ...d, ...data, updatedAt: new Date().toISOString() } : d
        )
        store.setDevices(devices)
        logStore.addLog({
          type: 'MESSAGE',
          level: 'info',
          source: 'MQTT',
          message: `디바이스 업데이트: ID=${data.id}`,
          detail: JSON.stringify(data),
        })
      } catch {
        logStore.addLog({
          type: 'MESSAGE',
          level: 'warn',
          source: 'MQTT',
          message: '파싱 불가 메시지 수신',
          detail: typeof event.data === 'string' ? event.data : null,
        })
      }
    }

    ws.onclose = () => {
      isConnected.value = false
      logStore.mqttStatus = 'disconnected'
      logStore.addLog({
        type: 'CONNECTION',
        level: 'warn',
        source: 'MQTT',
        message: '연결 종료',
        detail: null,
      })
      scheduleReconnect()
    }

    ws.onerror = () => {
      error.value = 'WebSocket connection error'
      isConnected.value = false
      logStore.mqttStatus = 'disconnected'
      logStore.addLog({
        type: 'ERROR',
        level: 'error',
        source: 'MQTT',
        message: 'WebSocket 연결 오류',
        detail: JSON.stringify({ url, error: 'Connection error' }),
      })
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    logStore.addLog({
      type: 'SYSTEM',
      level: 'info',
      source: 'MQTT',
      message: `${RECONNECT_DELAY / 1000}초 후 재연결 예정`,
      detail: null,
    })
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, RECONNECT_DELAY)
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws) {
      ws.close()
      ws = null
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    error,
    connect,
    disconnect,
  }
}
