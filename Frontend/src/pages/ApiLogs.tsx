import { useEffect, useState, useCallback } from 'react';
import { FileText, ChevronDown, ChevronRight, Trash2, RefreshCw, Search } from 'lucide-react';
import type { ApiLog, ApiLogListResponse } from '../types/apiLog';

const API_BASE = 'http://localhost:8000';

const METHOD_COLORS: Record<string, string> = {
  GET: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  POST: 'bg-green-500/20 text-green-400 border-green-500/30',
  PUT: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  DELETE: 'bg-red-500/20 text-red-400 border-red-500/30',
};

function statusColor(status: number | null): string {
  if (!status) return 'text-gray-500';
  if (status >= 200 && status < 300) return 'text-green-400';
  if (status >= 300 && status < 400) return 'text-yellow-400';
  if (status >= 400 && status < 500) return 'text-orange-400';
  return 'text-red-400';
}

function formatJson(raw: string | null): string {
  if (!raw) return '-';
  try {
    return JSON.stringify(JSON.parse(raw), null, 2);
  } catch {
    return raw;
  }
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

export default function ApiLogs() {
  const [logs, setLogs] = useState<ApiLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(20);
  const [method, setMethod] = useState('');
  const [search, setSearch] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), size: String(size) });
      if (method) params.set('method', method);
      if (search) params.set('search', search);
      const res = await fetch(`${API_BASE}/api/logs/?${params}`);
      if (!res.ok) throw new Error('Failed to fetch logs');
      const data: ApiLogListResponse = await res.json();
      setLogs(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('로그 조회 실패:', err);
    } finally {
      setLoading(false);
    }
  }, [page, size, method, search]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchLogs]);

  const handleDelete = async () => {
    if (!confirm('모든 API 로그를 삭제하시겠습니까?')) return;
    try {
      await fetch(`${API_BASE}/api/logs/`, { method: 'DELETE' });
      setPage(1);
      fetchLogs();
    } catch (err) {
      console.error('로그 삭제 실패:', err);
    }
  };

  const totalPages = Math.ceil(total / size);

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h2 className="text-2xl font-bold text-white">API 로그</h2>
        <p className="text-sm text-gray-500 mt-1">Mobius 서버와의 API 통신 로그를 확인하세요</p>
      </div>

      {/* 필터 바 */}
      <div className="flex flex-wrap items-center gap-3 bg-gray-900/50 border border-gray-800 rounded-2xl p-4">
        {/* 메서드 필터 */}
        <select
          value={method}
          onChange={(e) => { setMethod(e.target.value); setPage(1); }}
          className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500"
        >
          <option value="">전체 메서드</option>
          <option value="GET">GET</option>
          <option value="POST">POST</option>
          <option value="PUT">PUT</option>
          <option value="DELETE">DELETE</option>
        </select>

        {/* 검색 */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="URL 검색..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* 자동 새로고침 */}
        <button
          onClick={() => setAutoRefresh(!autoRefresh)}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm border transition-colors ${
            autoRefresh
              ? 'bg-blue-600/20 text-blue-400 border-blue-500/30'
              : 'bg-gray-800 text-gray-400 border-gray-700 hover:text-white'
          }`}
        >
          <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
          자동 새로고침
        </button>

        {/* 수동 새로고침 */}
        <button
          onClick={fetchLogs}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm bg-gray-800 text-gray-400 border border-gray-700 hover:text-white transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        {/* 전체 삭제 */}
        <button
          onClick={handleDelete}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm bg-red-600/10 text-red-400 border border-red-500/20 hover:bg-red-600/20 transition-colors"
        >
          <Trash2 className="w-4 h-4" />
          전체 삭제
        </button>
      </div>

      {/* 로그 테이블 */}
      <div className="bg-gray-900/50 border border-gray-800 rounded-2xl overflow-hidden">
        {/* 테이블 헤더 */}
        <div className="grid grid-cols-[40px_140px_70px_1fr_80px_80px] gap-2 px-4 py-3 text-xs font-medium text-gray-500 uppercase border-b border-gray-800">
          <span></span>
          <span>시각</span>
          <span>메서드</span>
          <span>URL</span>
          <span className="text-right">상태</span>
          <span className="text-right">소요</span>
        </div>

        {/* 로그 행 */}
        {loading && logs.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-gray-500">
            로딩 중...
          </div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-gray-500">
            <FileText className="w-8 h-8 mb-2 text-gray-600" />
            <span>기록된 API 로그가 없습니다</span>
          </div>
        ) : (
          logs.map((log) => (
            <div key={log.id}>
              {/* 요약 행 */}
              <div
                onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                className="grid grid-cols-[40px_140px_70px_1fr_80px_80px] gap-2 px-4 py-3 text-sm cursor-pointer hover:bg-gray-800/50 border-b border-gray-800/50 transition-colors"
              >
                <span className="flex items-center text-gray-600">
                  {expandedId === log.id ? (
                    <ChevronDown className="w-4 h-4" />
                  ) : (
                    <ChevronRight className="w-4 h-4" />
                  )}
                </span>
                <span className="text-gray-400 font-mono text-xs">
                  {formatTime(log.timestamp)}
                </span>
                <span>
                  <span className={`inline-block px-2 py-0.5 text-xs font-semibold rounded border ${METHOD_COLORS[log.method] || 'bg-gray-700 text-gray-300 border-gray-600'}`}>
                    {log.method}
                  </span>
                </span>
                <span className="text-gray-300 truncate font-mono text-xs" title={log.url}>
                  {log.url}
                </span>
                <span className={`text-right font-mono text-xs ${statusColor(log.responseStatus)}`}>
                  {log.responseStatus ?? '-'}
                </span>
                <span className="text-right text-gray-500 font-mono text-xs">
                  {log.durationMs != null ? `${log.durationMs}ms` : '-'}
                </span>
              </div>

              {/* 상세 확장 */}
              {expandedId === log.id && (
                <div className="px-6 py-4 bg-gray-800/30 border-b border-gray-800 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    {/* 요청 헤더 */}
                    <div>
                      <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">Request Headers</h4>
                      <pre className="bg-gray-900 rounded-lg p-3 text-xs text-gray-300 overflow-auto max-h-48 font-mono">
                        {formatJson(log.requestHeaders)}
                      </pre>
                    </div>
                    {/* 요청 바디 */}
                    <div>
                      <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">Request Body</h4>
                      <pre className="bg-gray-900 rounded-lg p-3 text-xs text-gray-300 overflow-auto max-h-48 font-mono">
                        {formatJson(log.requestBody)}
                      </pre>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">Response Body</h4>
                    <pre className="bg-gray-900 rounded-lg p-3 text-xs text-gray-300 overflow-auto max-h-64 font-mono">
                      {formatJson(log.responseBody)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">
            총 {total}건 중 {(page - 1) * size + 1}–{Math.min(page * size, total)}건
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 border border-gray-700 disabled:opacity-40 hover:text-white transition-colors"
            >
              이전
            </button>
            <span className="text-gray-400">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 border border-gray-700 disabled:opacity-40 hover:text-white transition-colors"
            >
              다음
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
