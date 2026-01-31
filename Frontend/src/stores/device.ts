import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Device, OutletPosition, PowerSummary, DailyPowerPoint } from '../types/device'

const mockDevices: Device[] = [
  {
    id: 1,
    name: '거실 TV',
    location: '거실',
    mqttTopic: 'iotcoss/device/1',
    isActive: true,
    currentPower: 120.5,
    temperature: 32.1,
    isOnline: true,
    createdAt: '2026-01-27T00:00:00Z',
    updatedAt: '2026-01-27T12:00:00Z',
  },
  {
    id: 2,
    name: '주방 전자레인지',
    location: '주방',
    mqttTopic: 'iotcoss/device/2',
    isActive: false,
    currentPower: 0,
    temperature: 25.3,
    isOnline: true,
    createdAt: '2026-01-27T00:00:00Z',
    updatedAt: '2026-01-27T12:00:00Z',
  },
  {
    id: 3,
    name: '침실 에어컨',
    location: '침실',
    mqttTopic: 'iotcoss/device/3',
    isActive: true,
    currentPower: 850.2,
    temperature: 38.7,
    isOnline: true,
    createdAt: '2026-01-27T00:00:00Z',
    updatedAt: '2026-01-27T12:00:00Z',
  },
  {
    id: 4,
    name: '서재 컴퓨터',
    location: '서재',
    mqttTopic: 'iotcoss/device/4',
    isActive: true,
    currentPower: 350.0,
    temperature: 41.2,
    isOnline: false,
    createdAt: '2026-01-27T00:00:00Z',
    updatedAt: '2026-01-27T12:00:00Z',
  },
  {
    id: 5,
    name: '욕실 온풍기',
    location: '욕실',
    mqttTopic: 'iotcoss/device/5',
    isActive: true,
    currentPower: 1200.0,
    temperature: 45.5,
    isOnline: true,
    createdAt: '2026-01-27T00:00:00Z',
    updatedAt: '2026-01-27T12:00:00Z',
  },
]

const mockOutletPositions: OutletPosition[] = [
  { id: 1, deviceId: 1, x: 22, y: 45, room: '거실' },
  { id: 2, deviceId: 2, x: 65, y: 30, room: '주방' },
  { id: 3, deviceId: 3, x: 22, y: 78, room: '침실' },
  { id: 4, deviceId: 4, x: 65, y: 78, room: '서재' },
  { id: 5, deviceId: 5, x: 88, y: 45, room: '욕실' },
]

const mockDailyPowerTotal: DailyPowerPoint[] = [
  { date: '1/24', power: 14.2 },
  { date: '1/25', power: 16.8 },
  { date: '1/26', power: 12.5 },
  { date: '1/27', power: 15.2 },
  { date: '1/28', power: 11.9 },
  { date: '1/29', power: 13.7 },
  { date: '1/30', power: 8.7 },
]

const mockDailyPowerByDevice: Record<number, DailyPowerPoint[]> = {
  1: [
    { date: '1/24', power: 2.8 },
    { date: '1/25', power: 3.1 },
    { date: '1/26', power: 2.4 },
    { date: '1/27', power: 3.0 },
    { date: '1/28', power: 2.2 },
    { date: '1/29', power: 2.7 },
    { date: '1/30', power: 1.5 },
  ],
  2: [
    { date: '1/24', power: 1.8 },
    { date: '1/25', power: 2.5 },
    { date: '1/26', power: 1.2 },
    { date: '1/27', power: 1.9 },
    { date: '1/28', power: 1.5 },
    { date: '1/29', power: 1.1 },
    { date: '1/30', power: 0.8 },
  ],
  3: [
    { date: '1/24', power: 5.1 },
    { date: '1/25', power: 6.3 },
    { date: '1/26', power: 4.8 },
    { date: '1/27', power: 5.5 },
    { date: '1/28', power: 4.2 },
    { date: '1/29', power: 5.8 },
    { date: '1/30', power: 3.6 },
  ],
  4: [
    { date: '1/24', power: 2.3 },
    { date: '1/25', power: 2.7 },
    { date: '1/26', power: 2.1 },
    { date: '1/27', power: 2.8 },
    { date: '1/28', power: 2.0 },
    { date: '1/29', power: 2.1 },
    { date: '1/30', power: 1.3 },
  ],
  5: [
    { date: '1/24', power: 2.2 },
    { date: '1/25', power: 2.2 },
    { date: '1/26', power: 2.0 },
    { date: '1/27', power: 2.0 },
    { date: '1/28', power: 2.0 },
    { date: '1/29', power: 2.0 },
    { date: '1/30', power: 1.5 },
  ],
}

function calcSummary(devices: Device[]): PowerSummary {
  return {
    totalPower: devices.reduce((sum, d) => sum + d.currentPower, 0),
    monthlyEnergy: 245.8,
    yesterdayEnergy: 13.7,
    todayEnergy: 8.7,
    activeDevices: devices.filter((d) => d.isActive).length,
    totalDevices: devices.length,
    avgTemperature:
      devices.reduce((sum, d) => sum + d.temperature, 0) / devices.length,
    savingsPercent: 18.5,
    estimatedCost: 32400,
    peakPower: 2520.7,
  }
}

export const useDeviceStore = defineStore('device', () => {
  const devices = ref<Device[]>(mockDevices)
  const outletPositions = ref<OutletPosition[]>(mockOutletPositions)
  const selectedDeviceId = ref<number | null>(null)
  const dailyPowerTotal = ref<DailyPowerPoint[]>(mockDailyPowerTotal)
  const dailyPowerByDevice = ref<Record<number, DailyPowerPoint[]>>(mockDailyPowerByDevice)

  const powerSummary = computed<PowerSummary>(() => calcSummary(devices.value))

  function addDevice(name: string, location: string) {
  // 1. 새 ID 계산
  const newId = devices.value.length > 0 
    ? Math.max(...devices.value.map(d => d.id)) + 1 
    : 1;

  // 2. 방 이름에 따른 초기 좌표 (사용자 편의를 위해 미리 세팅)
  const defaultCoords: Record<string, { x: number, y: number }> = {
    '거실': { x: 22, y: 45 },
    '주방': { x: 65, y: 30 },
    '침실': { x: 22, y: 78 },
    '서재': { x: 65, y: 78 },
    '욕실': { x: 88, y: 45 }
  };
  const coords = defaultCoords[location] || { x: 50, y: 50 };

  // 3. newDevice 객체 생성 (Device 인터페이스의 모든 필드 포함)
  const newDevice: Device = {
    id: newId,
    name: name,
    location: location,
    mqttTopic: `iotcoss/device/${newId}`,
    isActive: false,
    currentPower: 0,
    temperature: 20.0,
    isOnline: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  // 4. 스토어 상태(State) 업데이트
  devices.value.push(newDevice);

  // 5. 구조도 위치 데이터 추가
  outletPositions.value.push({
    id: newId,
    deviceId: newId,
    x: coords.x,
    y: coords.y,
    room: location
  });

  // 6. [중요] 차트 데이터 초기화 (이게 없으면 차트 컴포넌트에서 에러가 납니다)
  dailyPowerByDevice.value[newId] = [
    { date: '1/31', power: 0 }
  ];
}
  
  function removeDevice(id: number) {
    // 1. 디바이스 삭제
    devices.value = devices.value.filter(d => d.id !== id);
    // 2. 관련 위치 데이터 삭제
    outletPositions.value = outletPositions.value.filter(p => p.deviceId !== id);
    // 3. 선택된 디바이스가 삭제된 것이라면 선택 해제
    if (selectedDeviceId.value === id) selectedDeviceId.value = null;
  }

  function setDevices(newDevices: Device[]) {
    devices.value = newDevices
  }

  function toggleDevice(id: number) {
    devices.value = devices.value.map((d) =>
      d.id === id
        ? { ...d, isActive: !d.isActive, currentPower: d.isActive ? 0 : Math.random() * 500 + 50 }
        : d
    )
  }

  function selectDevice(id: number | null) {
    selectedDeviceId.value = id
  }

  function updatePosition(deviceId: number, x: number, y: number) {
  const pos = outletPositions.value.find(p => p.deviceId === deviceId)
  if (pos) {
    // 0~100 사이로 제한 (이미지 밖으로 나가지 않게)
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
    addDevice,
    removeDevice,
    setDevices,
    toggleDevice,
    selectDevice,
    updatePosition
  }
})
