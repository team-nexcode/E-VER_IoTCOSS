import { useEffect, useState } from 'react';
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

  useEffect(() => {
    const ping = async () => {
      const start = performance.now();
      try {
        const res = await fetch('http://localhost:8000/api/health');
        if (res.ok) {
          setResponseTime(Math.round(performance.now() - start));
          setStatus('online');
        } else {
          setStatus('offline');
          setResponseTime(null);
        }
      } catch {
        setStatus('offline');
        setResponseTime(null);
      }
    };
    ping();
    const interval = setInterval(ping, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className="fixed left-0 top-[60px] bottom-0 w-[250px] bg-[#111827] border-r border-gray-800 flex flex-col z-40">
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
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

      {/* 하단: 시스템 상태 */}
      <div className="p-4 border-t border-gray-800">
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
