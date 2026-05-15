import api from "../api";

export interface SystemSummary {
  total_workspaces: number;
  total_documents: number;
  total_chunks: number;
}

export interface ActivityItem {
  id: string;
  type: string;
  name: string;
  status: string;
  date: string;
}

export const getSystemSummary = async (): Promise<SystemSummary> => {
  const { data } = await api.get("/analytics/summary");
  return data;
};

export const getRecentActivity = async (): Promise<ActivityItem[]> => {
  const { data } = await api.get("/analytics/recent-activity");
  return data;
};

export interface ClusterResult {
  cluster_id: number;
  label: string;
  document_ids: string[];
  document_names: string[];
  keywords: string[];
}

export const getWorkspaceClusters = async (workspaceId: string): Promise<ClusterResult[]> => {
  const { data } = await api.get(`/analytics/${workspaceId}/clusters`);
  return data.clusters;
};
