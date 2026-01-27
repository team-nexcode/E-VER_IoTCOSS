import { BarChart3 } from 'lucide-react';

export default function PowerAnalysis() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">전력 분석</h2>
        <p className="text-sm text-gray-500 mt-1">전력 소비 패턴을 분석하세요</p>
      </div>
      <div className="flex items-center justify-center h-64 bg-gray-900/50 border border-gray-800 rounded-2xl">
        <div className="text-center">
          <BarChart3 className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500">전력 분석 페이지 (구현 예정)</p>
        </div>
      </div>
    </div>
  );
}
