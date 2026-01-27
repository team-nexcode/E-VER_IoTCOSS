import { Bell } from 'lucide-react';

export default function Alerts() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">알림</h2>
        <p className="text-sm text-gray-500 mt-1">시스템 알림 및 경고를 확인하세요</p>
      </div>
      <div className="flex items-center justify-center h-64 bg-gray-900/50 border border-gray-800 rounded-2xl">
        <div className="text-center">
          <Bell className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500">알림 페이지 (구현 예정)</p>
        </div>
      </div>
    </div>
  );
}
