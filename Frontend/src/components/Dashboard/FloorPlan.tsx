import { useDeviceStore } from '../../store/deviceStore';

interface FloorPlanProps {
  highlightedDeviceId: number | null;
  onSelectDevice: (id: number | null) => void;
}

export default function FloorPlan({ highlightedDeviceId, onSelectDevice }: FloorPlanProps) {
  const devices = useDeviceStore((s) => s.devices);
  const outletPositions = useDeviceStore((s) => s.outletPositions);

  const getDevice = (deviceId: number) => devices.find((d) => d.id === deviceId);

  return (
    <div className="h-full flex flex-col bg-gray-900/50 border border-gray-800 rounded-xl p-4 relative overflow-hidden">
      {/* 헤더 */}
      <div className="flex-shrink-0 flex items-center justify-between mb-3">
        <h3 className="text-base font-semibold text-white">실시간 모니터링</h3>
        <div className="flex items-center gap-3 text-[10px]">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-gray-400">활성</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
            <span className="text-gray-400">비활성</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            <span className="text-gray-400">오프라인</span>
          </div>
        </div>
      </div>

      {/* 구조도 SVG */}
      <div className="flex-1 min-h-0 relative">
        <svg
          viewBox="0 0 900 495"
          preserveAspectRatio="xMidYMid meet"
          className="w-full h-full"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* 배경 (클릭시 선택 해제) */}
          <rect x="0" y="0" width="900" height="495" rx="12" fill="#0c1222"
            className="cursor-pointer" onClick={() => onSelectDevice(null)} />

          {/* 외벽 */}
          <rect
            x="40" y="40" width="820" height="415" rx="4"
            fill="none" stroke="#334155" strokeWidth="3"
          />

          {/* 방 구분선 */}
          <line x1="40" y1="250" x2="680" y2="250" stroke="#334155" strokeWidth="2" />
          <line x1="380" y1="40" x2="380" y2="455" stroke="#334155" strokeWidth="2" />
          <line x1="680" y1="40" x2="680" y2="455" stroke="#334155" strokeWidth="2" />

          {/* 방 이름 */}
          <text x="210" y="85" textAnchor="middle" fill="#475569" fontSize="20" fontWeight="600">거실</text>
          <text x="210" y="107" textAnchor="middle" fill="#334155" fontSize="11">Living Room</text>
          <text x="530" y="85" textAnchor="middle" fill="#475569" fontSize="20" fontWeight="600">주방</text>
          <text x="530" y="107" textAnchor="middle" fill="#334155" fontSize="11">Kitchen</text>
          <text x="210" y="300" textAnchor="middle" fill="#475569" fontSize="20" fontWeight="600">침실</text>
          <text x="210" y="322" textAnchor="middle" fill="#334155" fontSize="11">Bedroom</text>
          <text x="530" y="300" textAnchor="middle" fill="#475569" fontSize="20" fontWeight="600">서재</text>
          <text x="530" y="322" textAnchor="middle" fill="#334155" fontSize="11">Study</text>
          <text x="790" y="230" textAnchor="middle" fill="#475569" fontSize="20" fontWeight="600">욕실</text>
          <text x="790" y="252" textAnchor="middle" fill="#334155" fontSize="11">Bathroom</text>

          {/* 문 */}
          <rect x="370" y="125" width="20" height="45" fill="#0c1222" />
          <line x1="370" y1="125" x2="370" y2="170" stroke="#60a5fa" strokeWidth="2" strokeDasharray="4" />
          <line x1="390" y1="125" x2="390" y2="170" stroke="#60a5fa" strokeWidth="2" strokeDasharray="4" />
          <rect x="370" y="330" width="20" height="45" fill="#0c1222" />
          <line x1="370" y1="330" x2="370" y2="375" stroke="#60a5fa" strokeWidth="2" strokeDasharray="4" />
          <line x1="390" y1="330" x2="390" y2="375" stroke="#60a5fa" strokeWidth="2" strokeDasharray="4" />
          <rect x="150" y="240" width="50" height="20" fill="#0c1222" />
          <line x1="150" y1="240" x2="200" y2="240" stroke="#60a5fa" strokeWidth="2" strokeDasharray="4" />
          <line x1="150" y1="260" x2="200" y2="260" stroke="#60a5fa" strokeWidth="2" strokeDasharray="4" />
          <rect x="670" y="130" width="20" height="45" fill="#0c1222" />
          <line x1="670" y1="130" x2="670" y2="175" stroke="#60a5fa" strokeWidth="2" strokeDasharray="4" />
          <line x1="690" y1="130" x2="690" y2="175" stroke="#60a5fa" strokeWidth="2" strokeDasharray="4" />
          <rect x="300" y="445" width="70" height="20" fill="#0c1222" />
          <line x1="300" y1="455" x2="370" y2="455" stroke="#f59e0b" strokeWidth="2.5" />
          <text x="335" y="483" textAnchor="middle" fill="#f59e0b" fontSize="11" fontWeight="500">현관</text>

          {/* 가구 */}
          <rect x="70" y="140" width="90" height="35" rx="5" fill="#1e293b" stroke="#334155" strokeWidth="1" />
          <text x="115" y="163" textAnchor="middle" fill="#334155" fontSize="10">소파</text>
          <rect x="280" y="140" width="8" height="50" rx="2" fill="#1e293b" stroke="#334155" strokeWidth="1" />
          <rect x="580" y="55" width="80" height="30" rx="4" fill="#1e293b" stroke="#334155" strokeWidth="1" />
          <text x="620" y="75" textAnchor="middle" fill="#334155" fontSize="10">싱크대</text>
          <rect x="395" y="55" width="40" height="50" rx="4" fill="#1e293b" stroke="#334155" strokeWidth="1" />
          <text x="415" y="84" textAnchor="middle" fill="#334155" fontSize="9">냉장고</text>
          <rect x="70" y="340" width="120" height="80" rx="5" fill="#1e293b" stroke="#334155" strokeWidth="1" />
          <text x="130" y="385" textAnchor="middle" fill="#334155" fontSize="10">침대</text>
          <rect x="480" y="370" width="100" height="55" rx="4" fill="#1e293b" stroke="#334155" strokeWidth="1" />
          <text x="530" y="402" textAnchor="middle" fill="#334155" fontSize="10">책상</text>
          <rect x="710" y="310" width="110" height="55" rx="8" fill="#1e293b" stroke="#334155" strokeWidth="1" />
          <text x="765" y="342" textAnchor="middle" fill="#334155" fontSize="10">욕조</text>
          <circle cx="740" cy="90" r="20" fill="#1e293b" stroke="#334155" strokeWidth="1" />
          <text x="740" y="94" textAnchor="middle" fill="#334155" fontSize="9">세면대</text>

          {/* 콘센트 마커 */}
          {outletPositions.map((pos) => {
            const device = getDevice(pos.deviceId);
            if (!device) return null;

            const cx = 40 + (pos.x / 100) * 820;
            const cy = 40 + (pos.y / 100) * 415;
            const isHighlighted = highlightedDeviceId === device.id;

            return (
              <g
                key={pos.id}
                className="cursor-pointer"
                onClick={() => onSelectDevice(isHighlighted ? null : device.id)}
              >
                {/* 선택 하이라이트 링 */}
                {isHighlighted && (
                  <>
                    <circle cx={cx} cy={cy} r="26" fill="none" stroke="#38bdf8" strokeWidth="2" opacity="0.6">
                      <animate attributeName="r" values="22;30;22" dur="1.5s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="0.7;0.2;0.7" dur="1.5s" repeatCount="indefinite" />
                    </circle>
                    <circle cx={cx} cy={cy} r="20" fill="#38bdf8" opacity="0.1" />
                  </>
                )}

                {/* 활성 디바이스 글로우 */}
                {device.isActive && device.isOnline && !isHighlighted && (
                  <circle cx={cx} cy={cy} r="18" fill="none" stroke="#22c55e" strokeWidth="1" opacity="0.3">
                    <animate attributeName="r" values="14;24;14" dur="2s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.4;0.1;0.4" dur="2s" repeatCount="indefinite" />
                  </circle>
                )}

                {/* 고전력 경고 */}
                {device.currentPower > 1000 && device.isOnline && !isHighlighted && (
                  <circle cx={cx} cy={cy} r="18" fill="none" stroke="#ef4444" strokeWidth="1.5" opacity="0.4">
                    <animate attributeName="r" values="16;26;16" dur="1.5s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.5;0.1;0.5" dur="1.5s" repeatCount="indefinite" />
                  </circle>
                )}

                {/* 콘센트 외부 원 */}
                <circle
                  cx={cx} cy={cy} r="13"
                  fill={!device.isOnline ? '#1e293b' : device.isActive ? '#052e16' : '#1e293b'}
                  stroke={isHighlighted ? '#38bdf8' : !device.isOnline ? '#ef4444' : device.isActive ? '#22c55e' : '#6b7280'}
                  strokeWidth={isHighlighted ? '3' : '2.5'}
                />

                {/* 콘센트 구멍 */}
                <circle cx={cx - 4} cy={cy - 2} r="2" fill={!device.isOnline ? '#ef4444' : device.isActive ? '#22c55e' : '#6b7280'} />
                <circle cx={cx + 4} cy={cy - 2} r="2" fill={!device.isOnline ? '#ef4444' : device.isActive ? '#22c55e' : '#6b7280'} />
                <rect x={cx - 2.5} y={cy + 2} width="5" height="2.5" rx="1" fill={!device.isOnline ? '#ef4444' : device.isActive ? '#22c55e' : '#6b7280'} />

                {/* 디바이스 이름 라벨 */}
                <text
                  x={cx} y={cy + 28}
                  textAnchor="middle"
                  fill={isHighlighted ? '#38bdf8' : '#64748b'}
                  fontSize="11"
                  fontWeight={isHighlighted ? '600' : '400'}
                >
                  {device.name}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
