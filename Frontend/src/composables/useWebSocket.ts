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
      message: `WebSocket 연결 시도: ${url}`,
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
        message: 'WebSocket 연결 성공',
        detail: JSON.stringify({
          url,
          broker: logStore.mqttBroker || '(조회 중)',
          topic: logStore.mqttTopic || '(조회 중)',
          timestamp: new Date().toISOString(),
        }),
      })
    }

    ws.onmessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data)

        if (message.type === 'pong') return

        // MQTT 브로커에서 실제로 수신한 메시지 → 상세 로그
        if (message.type === 'mqtt_message') {
          logStore.addLog({
            type: 'MESSAGE',
            level: 'info',
            source: 'MQTT',
            message: `토픽: ${message.topic}`,
            detail: JSON.stringify({
              broker: message.broker,
              topic: message.topic,
              subscribe_filter: message.subscribe_filter,
              payload: message.payload,
              received_at: new Date().toISOString(),
            }, null, 2),
          })
          return
        }

        // 디바이스 상태 (연결 직후 1회) → 디바이스 업데이트만, 로그 안 남김
        if (message.type === 'device_status' && Array.isArray(message.data)) {
          const now = new Date().toISOString()
          const updated: Device[] = message.data.map((d: Record<string, unknown>) => ({
            id: d.id as number,
            name: (d.name as string) ?? '',
            location: (d.location as string) ?? '',
            mqttTopic: `/oneM2M/req/Mobius/SOrigin_nexcode/${d.id}`,
            isActive: (d.is_active as boolean) ?? false,
            currentPower: (d.current_power as number) ?? 0,
            temperature: (d.temperature as number) ?? 0,
            isOnline: (d.is_online as boolean) ?? false,
            createdAt: now,
            updatedAt: now,
          }))
          store.setDevices(updated)
          return
        }

      } catch {
        logStore.addLog({
          type: 'ERROR',
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
