// 스케줄 타입 정의
export interface Schedule {
  id: number
  device_mac: string
  schedule_name: string
  start_time: string // "HH:MM:SS"
  end_time: string // "HH:MM:SS"
  enabled: boolean
  days_of_week: string // "0,1,2,3,4,5,6"
}

export interface ScheduleCreate {
  device_mac: string
  schedule_name: string
  start_time: string
  end_time: string
  enabled: boolean
  days_of_week: string
}
