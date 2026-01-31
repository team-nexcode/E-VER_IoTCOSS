import { ref, onUnmounted } from 'vue'
import { useDeviceStore } from '@/stores/device'
import type { Device } from '@/types/device'

export function useWebSocket(url: string) {
  const isConnected = ref(false)
  const error = ref<string | null>(null)
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  const RECONNECT_DELAY = 3000

  const store = useDeviceStore()

  function connect() {
    if (ws) {
      ws.close()
    }

    ws = new WebSocket(url)

    ws.onopen = () => {
      isConnected.value = true
      error.value = null
    }

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as Partial<Device> & { id: number }
        const devices = store.devices.map((d) =>
          d.id === data.id ? { ...d, ...data, updatedAt: new Date().toISOString() } : d
        )
        store.setDevices(devices)
      } catch {
        // ignore non-JSON messages
      }
    }

    ws.onclose = () => {
      isConnected.value = false
      scheduleReconnect()
    }

    ws.onerror = () => {
      error.value = 'WebSocket connection error'
      isConnected.value = false
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
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
