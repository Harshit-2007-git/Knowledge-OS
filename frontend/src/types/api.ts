// ── API Response Wrappers ─────────────────────────────────

export interface ApiError {
  detail: string;
  type?: string;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}
