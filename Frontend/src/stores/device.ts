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

  // 백엔드에서 전달받는 전력량 (kWh) 및 요금
  const monthlyEnergy = ref(0)
  const yesterdayEnergy = ref(0)
  const todayEnergy = ref(0)
  const estimatedCost = ref(0)

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
      monthlyEnergy: monthlyEnergy.value,
      yesterdayEnergy: yesterdayEnergy.value,
      todayEnergy: todayEnergy.value,
      activeDevices: activeCount,
      totalDevices: total,
      avgTemperature: avgTemp,
      savingsPercent: 0,
      estimatedCost: estimatedCost.value,
      peakPower: totalPower * 220,
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
      desiredState: (d.relay_status as string) === 'on', // 초기값은 실제 상태와 동일
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

  function setPowerSummary(data: Record<string, unknown>) {
    if (data.monthly_energy_kwh != null) monthlyEnergy.value = data.monthly_energy_kwh as number
    if (data.yesterday_energy_kwh != null) yesterdayEnergy.value = data.yesterday_energy_kwh as number
    if (data.today_energy_kwh != null) todayEnergy.value = data.today_energy_kwh as number
    if (data.estimated_cost != null) estimatedCost.value = data.estimated_cost as number
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

    // 오늘 전력량 실시간 갱신
    if (data.today_energy_kwh != null) todayEnergy.value = data.today_energy_kwh as number
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

  async function toggleDevicePower(deviceMac: string) {
    const device = devices.value.find((d) => d.deviceMac === deviceMac)
    if (!device) return

    const newState = !device.desiredState
    const newStateStr = newState ? 'on' : 'off'

    try {
      const response = await fetch('/api/devices/power/control', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mac_address: deviceMac,
          power_state: newStateStr,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        alert(`전원 제어에 실패했습니다.\n상태: ${response.status}\n에러: ${errorText}`)
      } else {
        // 성공 시 DB에서 최신 desired_state 가져오기
        await fetchDesiredStates()
      }
    } catch (error) {
      alert(`전원 제어 중 오류가 발생했습니다.\n${error}`)
    }
  }

  async function fetchDesiredStates() {
    try {
      const response = await fetch('/api/devices/power/status')
      if (response.ok) {
        const data = await response.json()
        // device_switch 테이블의 desired_state로 토글 상태 업데이트
        for (const statusItem of data.devices) {
          const device = devices.value.find((d) => d.deviceMac === statusItem.device_mac)
          if (device) {
            device.desiredState = statusItem.desired_state === 'on'
          }
        }
      }
    } catch (error) {
      console.error('제어 상태 조회 실패:', error)
    }
  }

  async function fetchDailyPower(days: number = 7, deviceMac?: string) {
    try {
      const url = deviceMac 
        ? `/api/power/daily?days=${days}&device_mac=${deviceMac}`
        : `/api/power/daily?days=${days}`
      const response = await fetch(url)
      if (response.ok) {
        const data = await response.json()
        if (deviceMac) {
          const device = devices.value.find(d => d.deviceMac === deviceMac)
          if (device) {
            dailyPowerByDevice.value[device.id] = data
          }
        } else {
          dailyPowerTotal.value = data
        }
      }
    } catch (error) {
      console.error('일별 전력량 조회 실패:', error)
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
    setPowerSummary,
    fetchDesiredStates,
    fetchDailyPower,
    updateDeviceSensor,
    selectDevice,
    updatePosition,
    toggleDevicePower,
  }
})
