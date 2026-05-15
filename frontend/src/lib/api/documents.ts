import api from "../api";

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type?: string;
  file_extension?: string;
  status: "pending" | "processing" | "completed" | "failed";
  error_message?: string;
  chunk_count: number;
  created_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
}

export const getDocuments = async (workspaceId: string, page = 1, pageSize = 20): Promise<DocumentListResponse> => {
  const { data } = await api.get(`/documents/`, {
    params: { workspace_id: workspaceId, page, page_size: pageSize },
  });
  return data;
};

export const uploadDocument = async (
  workspaceId: string,
  file: File,
  onUploadProgress?: (progressEvent: any) => void
): Promise<Document> => {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post(`/documents/upload`, formData, {
    params: { workspace_id: workspaceId },
    onUploadProgress,
  });
  return data;
};

export const deleteDocument = async (id: string): Promise<void> => {
  await api.delete(`/documents/${id}`);
};
