import api from "../api";

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  document_name: string;
  content: string;
  relevance_score: number;
  page_number?: number;
  metadata?: Record<string, unknown>;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  search_time_ms: number;
}

export interface SearchRequest {
  query: string;
  workspace_id: string;
  top_k?: number;
}

export const searchDocuments = async (payload: SearchRequest): Promise<SearchResponse> => {
  const { data } = await api.post("/search/", payload);
  return data;
};