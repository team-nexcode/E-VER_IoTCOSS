import { useState } from 'react';
import FloorPlan from '../components/Dashboard/FloorPlan';
import DevicePanel from '../components/Dashboard/DevicePanel';

export default function Dashboard() {
  const [selectedDeviceId, setSelectedDeviceId] = useState<number | null>(null);

  return (
    <div className="h-full flex gap-4">
      {/* 좌측: 집 구조도 */}
      <div className="flex-1 min-w-0">
        <FloorPlan
          highlightedDeviceId={selectedDeviceId}
          onSelectDevice={setSelectedDeviceId}
        />
      </div>

      {/* 우측: 디바이스 패널 */}
      <div className="w-80 flex-shrink-0">
        <DevicePanel
          selectedDeviceId={selectedDeviceId}
          onSelectDevice={setSelectedDeviceId}
        />
      </div>
    </div>
  );
}
