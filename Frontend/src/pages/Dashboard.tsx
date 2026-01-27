import { Zap, Plug, Thermometer, TrendingDown, Activity, BatteryCharging } from 'lucide-react';
import StatusCard from '../components/Dashboard/StatusCard';
import FloorPlan from '../components/Dashboard/FloorPlan';
import { useDeviceStore } from '../store/deviceStore';

export default function Dashboard() {
  const { powerSummary, devices } = useDeviceStore();
  const onlineDevices = devices.filter((d) => d.isOnline).length;

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div>
        <h2 className="text-2xl font-bold text-white">대시보드</h2>
        <p className="text-sm text-gray-500 mt-1">전체 시스템 현황을 한눈에 확인하세요</p>
      </div>

      {/* 상태 카드 그리드 */}
      <div className="grid grid-cols-2 md:grid-cols-3 2xl:grid-cols-6 gap-3">
        <StatusCard
          title="현재 총 전력"
          value={powerSummary.totalPower.toFixed(1)}
          unit="W"
          icon={<Zap className="w-5 h-5" />}
          color="yellow"
          trend={{ value: -5.2, isPositive: true }}
        />
        <StatusCard
          title="오늘 전력량"
          value={powerSummary.totalEnergy.toFixed(1)}
          unit="kWh"
          icon={<BatteryCharging className="w-5 h-5" />}
          color="blue"
          trend={{ value: -8.1, isPositive: true }}
        />
        <StatusCard
          title="활성 디바이스"
          value={`${powerSummary.activeDevices}/${powerSummary.totalDevices}`}
          icon={<Plug className="w-5 h-5" />}
          color="green"
        />
        <StatusCard
          title="온라인"
          value={`${onlineDevices}/${powerSummary.totalDevices}`}
          icon={<Activity className="w-5 h-5" />}
          color="purple"
        />
        <StatusCard
          title="평균 온도"
          value={powerSummary.avgTemperature.toFixed(1)}
          unit="°C"
          icon={<Thermometer className="w-5 h-5" />}
          color="red"
        />
        <StatusCard
          title="절감률"
          value={powerSummary.savingsPercent.toFixed(1)}
          unit="%"
          icon={<TrendingDown className="w-5 h-5" />}
          color="green"
          trend={{ value: 3.2, isPositive: true }}
        />
      </div>

      {/* 집 구조도 모니터링 */}
      <FloorPlan />
    </div>
  );
}
