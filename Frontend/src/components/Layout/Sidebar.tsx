import { useEffect, useState, useRef, useCallback } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Plug,
  BarChart3,
  Clock,
  Bell,
  FileText,
  Settings,
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '대시보드' },
  { to: '/devices', icon: Plug, label: '디바이스' },
  { to: '/power', icon: BarChart3, label: '전력 분석' },
  { to: '/schedule', icon: Clock, label: '스케줄' },
  { to: '/alerts', icon: Bell, label: '알림' },
  { to: '/api-logs', icon: FileText, label: 'API 로그' },
  { to: '/settings', icon: Settings, label: '설정' },
];

export default function Sidebar() {
  const [responseTime, setResponseTime] = useState<number | null>(null);
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [displayTime, setDisplayTime] = useState<string>('--:--:--');
  const [displayDate, setDisplayDate] = useState<string>('');
  const serverOffsetRef = useRef<number | null>(null);

  const syncTime = useCallback(async () => {
    const start = performance.now();
    try {
      const res = await fetch('/api/health');
      const elapsed = performance.now() - start;
      if (res.ok) {
        const data = await res.json();
        setResponseTime(Math.round(elapsed));
        setStatus('online');
        // 서버 시간과 로컬 시간의 차이 계산 (서버 기준으로 보정)
        const serverMs = new Date(data.server_time).getTime();
        const localMs = Date.now();
        serverOffsetRef.current = serverMs - localMs;
      } else {
        setStatus('offline');
        setResponseTime(null);
      }
    } catch {
      setStatus('offline');
      setResponseTime(null);
    }
  }, []);

  // 서버 동기화: 10초마다
  useEffect(() => {
    syncTime();
    const interval = setInterval(syncTime, 10000);
    return () => clearInterval(interval);
  }, [syncTime]);

  // 시계 표시: 1초마다
  useEffect(() => {
    const tick = () => {
      if (serverOffsetRef.current === null) return;
      const now = new Date(Date.now() + serverOffsetRef.current);
      setDisplayTime(
        now.toLocaleTimeString('ko-KR', { hour12: true, timeZone: 'Asia/Seoul' })
      );
      setDisplayDate(
        now.toLocaleDateString('ko-KR', {
          year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short',
          timeZone: 'Asia/Seoul',
        })
      );
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className="fixed left-0 top-[60px] bottom-0 w-[250px] bg-[#111827] border-r border-gray-800 flex flex-col z-40">
      <nav className="flex-1 py-4 px-3 space-y-2 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`
            }
          >
            <Icon className="w-5 h-5 flex-shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* 하단 */}
      <div className="p-4 border-t border-gray-800 space-y-3">
        {/* 서버 동기화 시계 */}
        <div className="bg-gray-800/50 rounded-xl p-3 text-center">
          {status === 'offline' ? (
            <>
              <p className="text-sm font-mono font-bold text-red-400">통신 오류</p>
              <p className="text-[10px] text-red-500/70 mt-1">서버 연결 실패</p>
            </>
          ) : serverOffsetRef.current !== null ? (
            <>
              <p className="text-lg font-mono font-bold text-white tracking-wider">{displayTime}</p>
              <p className="text-[10px] text-gray-500 mt-0.5">{displayDate}</p>
            </>
          ) : (
            <p className="text-sm font-mono text-yellow-400">동기화 중...</p>
          )}
        </div>

        {/* 시스템 상태 */}
        <div className="bg-gray-800/50 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-2 h-2 rounded-full ${
              status === 'online' ? 'bg-green-500 animate-pulse'
              : status === 'offline' ? 'bg-red-500'
              : 'bg-yellow-500 animate-pulse'
            }`} />
            <span className="text-xs text-gray-400">시스템 상태</span>
          </div>
          <p className={`text-xs font-medium ${
            status === 'online' ? 'text-green-400'
            : status === 'offline' ? 'text-red-400'
            : 'text-yellow-400'
          }`}>
            {status === 'online' ? '정상 운영 중' : status === 'offline' ? '서버 연결 실패' : '연결 중...'}
          </p>
          <p className="text-[10px] text-gray-600 mt-1">
            서버 응답: {status === 'online' && responseTime !== null ? `${responseTime}ms` : status === 'offline' ? '—' : '측정 중...'}
          </p>
        </div>
      </div>
    </aside>
  );
}
