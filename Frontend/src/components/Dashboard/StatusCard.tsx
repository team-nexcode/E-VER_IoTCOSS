import type { ReactNode } from 'react';

interface StatusCardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon: ReactNode;
  trend?: { value: number; isPositive: boolean };
  color: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
}

const colorMap = {
  blue: 'from-blue-600/20 to-blue-600/5 border-blue-500/20',
  green: 'from-green-600/20 to-green-600/5 border-green-500/20',
  yellow: 'from-yellow-600/20 to-yellow-600/5 border-yellow-500/20',
  red: 'from-red-600/20 to-red-600/5 border-red-500/20',
  purple: 'from-purple-600/20 to-purple-600/5 border-purple-500/20',
};

const iconBgMap = {
  blue: 'bg-blue-600/20 text-blue-400',
  green: 'bg-green-600/20 text-green-400',
  yellow: 'bg-yellow-600/20 text-yellow-400',
  red: 'bg-red-600/20 text-red-400',
  purple: 'bg-purple-600/20 text-purple-400',
};

export default function StatusCard({ title, value, unit, icon, trend, color }: StatusCardProps) {
  return (
    <div
      className={`bg-gradient-to-br ${colorMap[color]} border rounded-xl p-3 sm:p-4 transition-transform hover:scale-[1.02] min-w-0`}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs sm:text-sm text-gray-400 truncate mr-2">{title}</span>
        <div className={`w-8 h-8 sm:w-9 sm:h-9 rounded-lg flex-shrink-0 flex items-center justify-center ${iconBgMap[color]}`}>
          {icon}
        </div>
      </div>
      <div className="flex items-end gap-1.5">
        <span className="text-lg sm:text-xl font-bold text-white truncate">{value}</span>
        {unit && <span className="text-[10px] sm:text-xs text-gray-500 mb-0.5 flex-shrink-0">{unit}</span>}
      </div>
      {trend && (
        <div className="mt-1.5 flex items-center gap-1">
          <span className={`text-[10px] sm:text-xs font-medium ${trend.isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {trend.isPositive ? '+' : ''}{trend.value}%
          </span>
          <span className="text-[10px] sm:text-xs text-gray-600">전일 대비</span>
        </div>
      )}
    </div>
  );
}
