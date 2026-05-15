import api from "../api";

export interface Workspace {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export const getWorkspaces = async (): Promise<Workspace[]> => {
  const { data } = await api.get("/workspaces/");
  return data.workspaces;
};

export const createWorkspace = async (payload: { name: string; description?: string }): Promise<Workspace> => {
  const { data } = await api.post("/workspaces/", payload);
  return data;
};

export const deleteWorkspace = async (id: string): Promise<void> => {
  await api.delete(`/workspaces/${id}`);
};
