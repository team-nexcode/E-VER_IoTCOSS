import { create } from 'zustand';
import type { Device, OutletPosition, PowerSummary, DailyPowerPoint } from '../types/device';

// 더미 디바이스 데이터 (5개)
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
];

// 집 구조도 위의 콘센트 위치 (% 기준)
const mockOutletPositions: OutletPosition[] = [
  { id: 1, deviceId: 1, x: 22, y: 45, room: '거실' },
  { id: 2, deviceId: 2, x: 65, y: 30, room: '주방' },
  { id: 3, deviceId: 3, x: 22, y: 78, room: '침실' },
  { id: 4, deviceId: 4, x: 65, y: 78, room: '서재' },
  { id: 5, deviceId: 5, x: 88, y: 45, room: '욕실' },
];

// 일별 전력량 더미 데이터 (최근 7일)
const mockDailyPowerTotal: DailyPowerPoint[] = [
  { date: '1/24', power: 14.2 },
  { date: '1/25', power: 16.8 },
  { date: '1/26', power: 12.5 },
  { date: '1/27', power: 15.2 },
  { date: '1/28', power: 11.9 },
  { date: '1/29', power: 13.7 },
  { date: '1/30', power: 8.7 },
];

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
};

interface DeviceStore {
  devices: Device[];
  outletPositions: OutletPosition[];
  selectedDeviceId: number | null;
  powerSummary: PowerSummary;
  dailyPowerTotal: DailyPowerPoint[];
  dailyPowerByDevice: Record<number, DailyPowerPoint[]>;
  setDevices: (devices: Device[]) => void;
  toggleDevice: (id: number) => void;
  selectDevice: (id: number | null) => void;
  updatePowerSummary: () => void;
}

const calcSummary = (devices: Device[]): PowerSummary => ({
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
});

export const useDeviceStore = create<DeviceStore>((set) => ({
  devices: mockDevices,
  outletPositions: mockOutletPositions,
  selectedDeviceId: null,
  powerSummary: calcSummary(mockDevices),
  dailyPowerTotal: mockDailyPowerTotal,
  dailyPowerByDevice: mockDailyPowerByDevice,

  setDevices: (devices) =>
    set({ devices, powerSummary: calcSummary(devices) }),

  toggleDevice: (id) =>
    set((state) => {
      const newDevices = state.devices.map((d) =>
        d.id === id
          ? { ...d, isActive: !d.isActive, currentPower: d.isActive ? 0 : Math.random() * 500 + 50 }
          : d
      );
      return { devices: newDevices, powerSummary: calcSummary(newDevices) };
    }),

  selectDevice: (id) => set({ selectedDeviceId: id }),

  updatePowerSummary: () =>
    set((state) => ({ powerSummary: calcSummary(state.devices) })),
}));
