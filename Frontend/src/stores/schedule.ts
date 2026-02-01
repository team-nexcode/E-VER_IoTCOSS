import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Schedule, ScheduleCreate } from '../types/schedule'

export const useScheduleStore = defineStore('schedule', () => {
  const schedules = ref<Schedule[]>([])
  const loading = ref(false)

  async function fetchSchedules(deviceMac?: string) {
    loading.value = true
    try {
      const url = deviceMac
        ? `/api/schedules?device_mac=${deviceMac}`
        : '/api/schedules'
      const response = await fetch(url)
      if (response.ok) {
        schedules.value = await response.json()
      } else {
        throw new Error('스케줄 조회 실패')
      }
    } catch (error) {
      console.error('스케줄 조회 오류:', error)
      alert('스케줄을 불러올 수 없습니다.')
    } finally {
      loading.value = false
    }
  }

  async function createSchedule(schedule: ScheduleCreate) {
    try {
      const response = await fetch('/api/schedules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(schedule),
      })
      
      if (response.ok) {
        await fetchSchedules()
        return true
      } else {
        const error = await response.text()
        alert(`스케줄 생성 실패: ${error}`)
        return false
      }
    } catch (error) {
      console.error('스케줄 생성 오류:', error)
      alert('스케줄 생성 중 오류가 발생했습니다.')
      return false
    }
  }

  async function deleteSchedule(scheduleId: number) {
    try {
      const response = await fetch(`/api/schedules/${scheduleId}`, {
        method: 'DELETE',
      })
      
      if (response.ok) {
        await fetchSchedules()
        return true
      } else {
        const error = await response.text()
        alert(`스케줄 삭제 실패: ${error}`)
        return false
      }
    } catch (error) {
      console.error('스케줄 삭제 오류:', error)
      alert('스케줄 삭제 중 오류가 발생했습니다.')
      return false
    }
  }

  async function toggleSchedule(scheduleId: number, enabled: boolean) {
    try {
      const response = await fetch(`/api/schedules/${scheduleId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      })
      
      if (response.ok) {
        await fetchSchedules()
        return true
      } else {
        const error = await response.text()
        alert(`스케줄 수정 실패: ${error}`)
        return false
      }
    } catch (error) {
      console.error('스케줄 수정 오류:', error)
      alert('스케줄 수정 중 오류가 발생했습니다.')
      return false
    }
  }

  return {
    schedules,
    loading,
    fetchSchedules,
    createSchedule,
    deleteSchedule,
    toggleSchedule,
  }
})
