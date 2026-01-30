import { useState } from 'react';
import { BatteryCharging, Clock, Zap, TrendingDown, Banknote, Activity } from 'lucide-react';
import StatusCard from '../components/Dashboard/StatusCard';
import FloorPlan from '../components/Dashboard/FloorPlan';
import DevicePanel from '../components/Dashboard/DevicePanel';
import { useDeviceStore } from '../store/deviceStore';

export default function Dashboard() {
  const [selectedDeviceId, setSelectedDeviceId] = useState<number | null>(null);
  const { powerSummary } = useDeviceStore();

  return (
    <div className="h-[calc(100vh-60px-2rem)] flex flex-col gap-4">
      {/* 상단: 요약 카드 */}
      <div className="flex-shrink-0 flex items-stretch gap-3 ml-1">
        <div className="flex-1 min-w-0">
          <StatusCard
            title="이번달 누적 전력량"
            value={powerSummary.monthlyEnergy.toFixed(1)}
            unit="kWh"
            icon={<BatteryCharging className="w-5 h-5" />}
            color="blue"
          />
        </div>
        <div className="flex-1 min-w-0">
          <StatusCard
            title="어제 전력량"
            value={powerSummary.yesterdayEnergy.toFixed(1)}
            unit="kWh"
            icon={<Clock className="w-5 h-5" />}
            color="yellow"
          />
        </div>
        <div className="flex-1 min-w-0">
          <StatusCard
            title="오늘 전력량"
            value={powerSummary.todayEnergy.toFixed(1)}
            unit="kWh"
            icon={<Zap className="w-5 h-5" />}
            color="green"
            trend={{ value: -12.5, isPositive: true }}
          />
        </div>
        <div className="flex-1 min-w-0">
          <StatusCard
            title="예상 절감률"
            value={powerSummary.savingsPercent.toFixed(1)}
            unit="%"
            icon={<TrendingDown className="w-5 h-5" />}
            color="green"
            trend={{ value: 3.2, isPositive: true }}
          />
        </div>

        {/* 구분선 */}
        <div className="w-px bg-gray-700/50 self-stretch my-2 flex-shrink-0" />

        <div className="flex-1 min-w-0">
          <StatusCard
            title="예상 전기요금"
            value={powerSummary.estimatedCost.toLocaleString()}
            unit="원"
            icon={<Banknote className="w-5 h-5" />}
            color="purple"
          />
        </div>
        <div className="flex-1 min-w-0">
          <StatusCard
            title="피크 전력"
            value={powerSummary.peakPower.toLocaleString()}
            unit="W"
            icon={<Activity className="w-5 h-5" />}
            color="red"
          />
        </div>
      </div>

      {/* 하단: 구조도(좌) + 디바이스 패널(우) */}
      <div className="flex-1 min-h-0 flex gap-4">
        <div className="flex-1 min-w-0">
          <FloorPlan
            highlightedDeviceId={selectedDeviceId}
            onSelectDevice={setSelectedDeviceId}
          />
        </div>
        <div className="w-80 flex-shrink-0">
          <DevicePanel
            selectedDeviceId={selectedDeviceId}
            onSelectDevice={setSelectedDeviceId}
          />
        </div>
      </div>
    </div>
  );
}
