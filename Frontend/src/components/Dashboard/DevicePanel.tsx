import { Zap, Thermometer, Power, Wifi, WifiOff } from 'lucide-react';
import { useDeviceStore } from '../../store/deviceStore';

interface DevicePanelProps {
  selectedDeviceId: number | null;
  onSelectDevice: (id: number | null) => void;
}

export default function DevicePanel({ selectedDeviceId, onSelectDevice }: DevicePanelProps) {
  const devices = useDeviceStore((s) => s.devices);
  const toggleDevice = useDeviceStore((s) => s.toggleDevice);

  return (
    <div className="h-full flex flex-col bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
      {/* 헤더 */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-gray-800">
        <h3 className="text-sm font-semibold text-white">디바이스 목록</h3>
        <p className="text-[10px] text-gray-500 mt-0.5">클릭하여 구조도에서 위치 확인</p>
      </div>

      {/* 디바이스 카드 목록 (스크롤) */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-3">
        {devices.map((device) => {
          const isSelected = selectedDeviceId === device.id;
          return (
            <div
              key={device.id}
              onClick={() => onSelectDevice(isSelected ? null : device.id)}
              className={`rounded-xl border px-4 py-4 cursor-pointer transition-all duration-200 ${
                isSelected
                  ? 'bg-sky-500/10 border-sky-500/40 shadow-lg shadow-sky-500/5'
                  : 'bg-gray-800/40 border-gray-700/50 hover:bg-gray-800/70 hover:border-gray-600'
              }`}
            >
              {/* 디바이스 헤더 */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 min-w-0">
                  {device.isOnline ? (
                    <Wifi className="w-3.5 h-3.5 text-green-400 flex-shrink-0" />
                  ) : (
                    <WifiOff className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                  )}
                  <span className={`text-sm font-medium truncate ${isSelected ? 'text-sky-300' : 'text-white'}`}>
                    {device.name}
                  </span>
                </div>
                <span className="text-[10px] text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded-full flex-shrink-0">
                  {device.location}
                </span>
              </div>

              {/* 전력 / 온도 */}
              <div className="flex items-center gap-4 mb-3">
                <div className="flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-yellow-400" />
                  <span className={`text-xs font-semibold ${device.currentPower > 500 ? 'text-red-400' : device.currentPower > 0 ? 'text-yellow-400' : 'text-gray-500'}`}>
                    {device.currentPower.toFixed(1)} W
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Thermometer className="w-3.5 h-3.5 text-orange-400" />
                  <span className={`text-xs font-semibold ${device.temperature > 40 ? 'text-red-400' : device.temperature > 35 ? 'text-orange-400' : 'text-green-400'}`}>
                    {device.temperature.toFixed(1)}°C
                  </span>
                </div>
              </div>

              {/* On/Off 토글 */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Power className="w-3.5 h-3.5 text-blue-400" />
                  <span className="text-[10px] text-gray-400">전원</span>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); toggleDevice(device.id); }}
                  disabled={!device.isOnline}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-medium transition-all ${
                    !device.isOnline
                      ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                      : device.isActive
                      ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30 border border-green-500/30'
                      : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700 border border-gray-600/30'
                  }`}
                >
                  <div className={`w-1.5 h-1.5 rounded-full ${device.isActive && device.isOnline ? 'bg-green-400' : 'bg-gray-500'}`} />
                  {!device.isOnline ? '오프라인' : device.isActive ? 'ON' : 'OFF'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
