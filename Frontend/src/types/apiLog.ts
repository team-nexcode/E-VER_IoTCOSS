export interface ApiLog {
  id: number;
  timestamp: string;
  method: string;
  url: string;
  requestHeaders: string | null;
  requestBody: string | null;
  responseStatus: number | null;
  responseBody: string | null;
  durationMs: number | null;
  direction: string;
}

export interface ApiLogListResponse {
  items: ApiLog[];
  total: number;
  page: number;
  size: number;
}
