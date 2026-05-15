// ── Chat Types ────────────────────────────────────────────

export interface Citation {
  chunk_id: string;
  document_id: string;
  document_name: string;
  content: string;
  page_number?: number;
  relevance_score: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  message_index: number;
  citations?: Citation[];
  model_name?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  model_name?: string;
  workspace_id: string;
  user_id: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  workspace_id: string;
  model_name?: string;
  top_k?: number;
  temperature?: number;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  document_name: string;
  content: string;
  page_number?: number;
  relevance_score: number;
  metadata?: Record<string, unknown>;
}

export interface ModelInfo {
  name: string;
  size?: string;
  modified_at?: string;
  family?: string;
  parameter_size?: string;
}
