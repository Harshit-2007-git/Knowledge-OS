// ── Document Types ────────────────────────────────────────

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type?: string;
  file_extension?: string;
  page_count?: number;
  status: "pending" | "processing" | "completed" | "failed";
  error_message?: string;
  chunk_count: number;
  workspace_id: string;
  uploaded_by?: string;
  created_at: string;
  updated_at: string;
}

export interface Workspace {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  settings?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  document_count?: number;
}
