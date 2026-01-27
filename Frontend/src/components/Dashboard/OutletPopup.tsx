import { Power, Thermometer, Zap, Wifi, WifiOff } from 'lucide-react';
import type { Device } from '../../types/device';
import { useDeviceStore } from '../../store/deviceStore';

interface OutletPopupProps {
  device: Device;
  x: number;
  y: number;
}

export default function OutletPopup({ device, x, y }: OutletPopupProps) {
  const toggleDevice = useDeviceStore((s) => s.toggleDevice);

  const isLeft = x > 50;
  const isTop = y > 60;

  return (
    <div
      className="absolute z-30 pointer-events-auto"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        transform: `translate(${isLeft ? '-100%' : '0'}, ${isTop ? '-100%' : '0'})`,
      }}
    >
      {/* 콘센트 마커 */}
      <div className="relative">
        {/* 연결선 */}
        <div
          className={`absolute w-px h-8 ${device.isOnline ? (device.isActive ? 'bg-green-500' : 'bg-gray-600') : 'bg-red-500'}`}
          style={{
            left: isLeft ? '100%' : '0',
            top: isTop ? '100%' : '-32px',
          }}
        />

        {/* 말풍선 팝업 */}
        <div
          className={`w-44 sm:w-52 rounded-xl border shadow-2xl backdrop-blur-sm transition-all duration-300 ${
            device.isOnline
              ? device.isActive
                ? 'bg-gray-900/95 border-green-500/30 shadow-green-500/10'
                : 'bg-gray-900/95 border-gray-600/30'
              : 'bg-gray-900/95 border-red-500/30 shadow-red-500/10'
          }`}
        >
          {/* 헤더 */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700/50">
            <div className="flex items-center gap-1.5 min-w-0">
              {device.isOnline ? (
                <Wifi className="w-3 h-3 text-green-400 flex-shrink-0" />
              ) : (
                <WifiOff className="w-3 h-3 text-red-400 flex-shrink-0" />
              )}
              <span className="text-xs sm:text-sm font-semibold text-white truncate">{device.name}</span>
            </div>
            <span className="text-[9px] sm:text-[10px] text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded-full flex-shrink-0 ml-1">
              {device.location}
            </span>
          </div>

          {/* 데이터 */}
          <div className="px-3 py-2.5 space-y-2">
            {/* 전력량 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-yellow-400" />
                <span className="text-xs text-gray-400">전력</span>
              </div>
              <span className={`text-sm font-bold ${device.currentPower > 500 ? 'text-red-400' : device.currentPower > 0 ? 'text-yellow-400' : 'text-gray-500'}`}>
                {device.currentPower.toFixed(1)} W
              </span>
            </div>

            {/* 온도 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Thermometer className="w-4 h-4 text-orange-400" />
                <span className="text-xs text-gray-400">온도</span>
              </div>
              <span className={`text-sm font-bold ${device.temperature > 40 ? 'text-red-400' : device.temperature > 35 ? 'text-orange-400' : 'text-green-400'}`}>
                {device.temperature.toFixed(1)}°C
              </span>
            </div>

            {/* On/Off 상태 + 토글 */}
            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2">
                <Power className="w-4 h-4 text-blue-400" />
                <span className="text-xs text-gray-400">상태</span>
              </div>
              <button
                onClick={() => toggleDevice(device.id)}
                disabled={!device.isOnline}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all ${
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
        </div>
      </div>
    </div>
  );
}
