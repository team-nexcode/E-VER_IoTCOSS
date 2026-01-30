import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useDeviceStore } from '../../store/deviceStore';

interface PowerChartProps {
  selectedDeviceId: number | null;
}

export default function PowerChart({ selectedDeviceId }: PowerChartProps) {
  const devices = useDeviceStore((s) => s.devices);
  const dailyPowerTotal = useDeviceStore((s) => s.dailyPowerTotal);
  const dailyPowerByDevice = useDeviceStore((s) => s.dailyPowerByDevice);

  const selectedDevice = selectedDeviceId ? devices.find((d) => d.id === selectedDeviceId) : null;
  const data = selectedDeviceId ? (dailyPowerByDevice[selectedDeviceId] ?? dailyPowerTotal) : dailyPowerTotal;
  const barColor = selectedDeviceId ? '#38bdf8' : '#3b82f6';
  const title = selectedDevice ? `${selectedDevice.name} - 일별 전력량` : '일별 총 전력량';

  return (
    <div className="h-full flex flex-col">
      <div className="flex-shrink-0 px-3 pt-3 pb-1">
        <span className="text-[11px] font-medium text-gray-400">{title}</span>
      </div>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: '#64748b', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              width={40}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              labelStyle={{ color: '#94a3b8' }}
              itemStyle={{ color: '#e2e8f0' }}
              formatter={(value) => [`${value} kWh`, '전력량']}
            />
            <Bar
              dataKey="power"
              fill={barColor}
              radius={[3, 3, 0, 0]}
              maxBarSize={28}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
