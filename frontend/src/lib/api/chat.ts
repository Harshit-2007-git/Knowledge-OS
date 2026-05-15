import api from "../api";

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  message_index: number;
  citations?: any;
  model_name?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  workspace_id: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface ChatRequest {
  workspace_id: string;
  message: string;
  conversation_id?: string;
  model_name?: string;
}

export const getConversations = async (workspaceId: string): Promise<Conversation[]> => {
  const { data } = await api.get(`/chat/conversations`, { params: { workspace_id: workspaceId } });
  return data.conversations;
};

export const getConversation = async (conversationId: string): Promise<Conversation> => {
  const { data } = await api.get(`/chat/conversations/${conversationId}`);
  return data;
};

export const sendMessage = async (payload: ChatRequest): Promise<Message> => {
  const { data } = await api.post(`/chat/`, payload);
  return data;
};
