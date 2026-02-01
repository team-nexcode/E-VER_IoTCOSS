import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Device, OutletPosition, PowerSummary, DailyPowerPoint } from '../types/device'

const defaultCoords: Record<string, { x: number; y: number }> = {
  '거실': { x: 22, y: 45 },
  '주방': { x: 65, y: 30 },
  '침실': { x: 22, y: 78 },
  '서재': { x: 65, y: 78 },
  '욕실': { x: 88, y: 45 },
}

let nextDefaultX = 50
let nextDefaultY = 50

function getDefaultCoords(location: string): { x: number; y: number } {
  if (defaultCoords[location]) {
    return defaultCoords[location]
  }
  const coords = { x: nextDefaultX, y: nextDefaultY }
  nextDefaultX = ((nextDefaultX + 15) % 80) + 10
  nextDefaultY = ((nextDefaultY + 15) % 80) + 10
  return coords
}

export const useDeviceStore = defineStore('device', () => {
  const devices = ref<Device[]>([])
  const outletPositions = ref<OutletPosition[]>([])
  const selectedDeviceId = ref<number | null>(null)
  const dailyPowerTotal = ref<DailyPowerPoint[]>([])
  const dailyPowerByDevice = ref<Record<number, DailyPowerPoint[]>>({})

  const powerSummary = computed<PowerSummary>(() => {
    const devs = devices.value
    const total = devs.length
    const activeCount = devs.filter((d) => d.isActive).length
    const totalPower = devs.reduce((sum, d) => sum + d.currentPower, 0)
    const avgTemp = total > 0
      ? devs.reduce((sum, d) => sum + d.temperature, 0) / total
      : 0

    return {
      totalPower,
      monthlyEnergy: 0,
      yesterdayEnergy: 0,
      todayEnergy: 0,
      activeDevices: activeCount,
      totalDevices: total,
      avgTemperature: avgTemp,
      savingsPercent: 0,
      estimatedCost: 0,
      peakPower: 0,
    }
  })

  function setDevices(rawList: Record<string, unknown>[]) {
    const now = new Date().toISOString()

    devices.value = rawList.map((d) => ({
      id: d.id as number,
      name: (d.device_name as string) ?? '',
      deviceMac: (d.device_mac as string) ?? '',
      location: (d.location as string) ?? '',
      isActive: (d.relay_status as string) === 'on',
      currentPower: (d.energy_amp as number) ?? 0,
      temperature: (d.temperature as number) ?? 0,
      humidity: (d.humidity as number) ?? 0,
      relayStatus: (d.relay_status as string) ?? null,
      isOnline: (d.is_online as boolean) ?? false,
      updatedAt: (d.timestamp as string) ?? now,
    }))

    // 새 디바이스에 대해 outletPosition 자동 생성 (기존 위치는 유지)
    const existingIds = new Set(outletPositions.value.map((p) => p.deviceId))
    for (const dev of devices.value) {
      if (!existingIds.has(dev.id)) {
        const coords = getDefaultCoords(dev.location)
        outletPositions.value.push({
          id: dev.id,
          deviceId: dev.id,
          x: coords.x,
          y: coords.y,
          room: dev.location,
        })
      }
    }

    // 더 이상 존재하지 않는 디바이스의 위치 데이터 제거
    const deviceIds = new Set(devices.value.map((d) => d.id))
    outletPositions.value = outletPositions.value.filter((p) => deviceIds.has(p.deviceId))
  }

  function updateDeviceSensor(data: Record<string, unknown>) {
    const mac = data.device_mac as string
    if (!mac) return

    const device = devices.value.find((d) => d.deviceMac === mac)
    if (device) {
      if (data.temperature != null) device.temperature = data.temperature as number
      if (data.humidity != null) device.humidity = data.humidity as number
      if (data.energy_amp != null) device.currentPower = data.energy_amp as number
      if (data.relay_status !== undefined) {
        device.relayStatus = data.relay_status as string | null
        device.isActive = (data.relay_status as string) === 'on'
      }
      if (data.timestamp) device.updatedAt = data.timestamp as string
      if (data.is_online !== undefined) device.isOnline = data.is_online as boolean
    }
  }

  function selectDevice(id: number | null) {
    selectedDeviceId.value = id
  }

  function updatePosition(deviceId: number, x: number, y: number) {
    const pos = outletPositions.value.find((p) => p.deviceId === deviceId)
    if (pos) {
      pos.x = Math.max(0, Math.min(100, x))
      pos.y = Math.max(0, Math.min(100, y))
    }
  }

  return {
    devices,
    outletPositions,
    selectedDeviceId,
    powerSummary,
    dailyPowerTotal,
    dailyPowerByDevice,
    setDevices,
    updateDeviceSensor,
    selectDevice,
    updatePosition,
  }
})
