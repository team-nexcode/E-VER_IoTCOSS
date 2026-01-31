export type LogType = 'CONNECTION' | 'MESSAGE' | 'ERROR' | 'SYSTEM'
export type LogLevel = 'info' | 'warn' | 'error'

export interface SystemLog {
  id: number
  timestamp: string
  type: LogType
  level: LogLevel
  source: string       // 'MQTT', 'Server', 'App'
  message: string      // 한 줄 요약
  detail: string | null // JSON 상세 (행 확장 시 표시)
}

export interface SystemLogListResponse {
  items: SystemLog[]
  total: number
  page: number
  size: number
}
