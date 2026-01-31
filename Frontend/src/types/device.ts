export interface Device {
  id: number;
  name: string;
  deviceMac: string;
  location: string;
  isActive: boolean;
  currentPower: number;
  temperature: number;
  humidity: number;
  relayStatus: string | null;
  isOnline: boolean;
  updatedAt: string;
}

export interface OutletPosition {
  id: number;
  deviceId: number;
  x: number;
  y: number;
  room: string;
}

export interface PowerLog {
  id: number;
  deviceId: number;
  powerWatts: number;
  voltage: number;
  currentAmps: number;
  temperature: number;
  recordedAt: string;
}

export interface PowerSummary {
  totalPower: number;
  monthlyEnergy: number;
  yesterdayEnergy: number;
  todayEnergy: number;
  activeDevices: number;
  totalDevices: number;
  avgTemperature: number;
  savingsPercent: number;
  estimatedCost: number;
  peakPower: number;
}

export interface DailyPowerPoint {
  date: string;
  power: number;
}
