export interface Device {
  id: number;
  name: string;
  location: string;
  mqttTopic: string;
  isActive: boolean;
  currentPower: number;
  temperature: number;
  isOnline: boolean;
  createdAt: string;
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
  totalEnergy: number;
  activeDevices: number;
  totalDevices: number;
  avgTemperature: number;
  savingsPercent: number;
}
