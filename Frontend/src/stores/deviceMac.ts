import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { DeviceMac } from '@/types/deviceMac'

export const useDeviceMacStore = defineStore('deviceMac', () => {
  const devices = ref<DeviceMac[]>([])
  const loading = ref(false)

  async function fetchDevices() {
    loading.value = true
    try {
      const res = await fetch('/api/device_mac/')
      if (!res.ok) return
      const data = await res.json()
      devices.value = (data.items || []).map((item: Record<string, unknown>) => ({
        id: item.id as number,
        deviceName: item.device_name as string,
        deviceMac: item.device_mac as string,
        location: item.location as string,
        createdAt: item.created_at as string,
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
    await fetchDevices()
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
    await fetchDevices()
  }

  async function deleteDevice(id: number) {
    const res = await fetch(`/api/device_mac/${id}`, { method: 'DELETE' })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || '삭제 실패')
    }
    await fetchDevices()
  }

  return {
    devices,
    loading,
    fetchDevices,
    addDevice,
    updateDevice,
    deleteDevice,
  }
})
