import api from "../api";

export interface SearchResult {
  document_id: string;
  filename: string;
  content: string;
  score: number;
  chunk_index: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  search_time_ms: number;
}

export interface SearchRequest {
  query: string;
  workspace_id?: string;
  top_k?: number;
}

export const searchDocuments = async (payload: SearchRequest): Promise<SearchResponse> => {
  const { data } = await api.post("/search/", payload);
  return data;
};
