import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { DeviceMac } from '@/types/deviceMac'

export const useDeviceMacStore = defineStore('deviceMac', () => {
  const deviceMacs = ref<DeviceMac[]>([])
  const loading = ref(false)

  async function fetchDeviceMacs() {
    loading.value = true
    try {
      const res = await fetch('/api/device_mac/')
      if (!res.ok) return
      const data = await res.json()
      deviceMacs.value = (data.items || []).map((item: Record<string, unknown>) => ({
        id: item.id as number,
        device_name: item.device_name as string,
        device_mac: item.device_mac as string,
        location: item.location as string,
        created_at: item.created_at as string,
      }))
    } catch {
      // silent
    } finally {
      loading.value = false
    }
  }

  async function addDevice(data: { deviceName: string; deviceMac: string; location: string }) {
    const res = await fetch('/api/device_mac/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        device_name: data.deviceName,
        device_mac: data.deviceMac,
        location: data.location,
      }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || '등록 실패')
    }
    await fetchDeviceMacs()
  }

  async function updateDevice(id: number, data: { deviceName?: string; deviceMac?: string; location?: string }) {
    const body: Record<string, string> = {}
    if (data.deviceName !== undefined) body.device_name = data.deviceName
    if (data.deviceMac !== undefined) body.device_mac = data.deviceMac
    if (data.location !== undefined) body.location = data.location

    const res = await fetch(`/api/device_mac/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || '수정 실패')
    }
    await fetchDeviceMacs()
  }

  async function deleteDevice(id: number) {
    const res = await fetch(`/api/device_mac/${id}`, { method: 'DELETE' })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || '삭제 실패')
    }
    await fetchDeviceMacs()
  }

  return {
    deviceMacs,
    loading,
    fetchDeviceMacs,
    addDevice,
    updateDevice,
    deleteDevice,
  }
})
