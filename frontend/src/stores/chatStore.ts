import { create } from "zustand";
import type { Message, Conversation, ModelInfo } from "@/types/chat";

interface ChatState {
  conversations: Conversation[];
  activeConversation: Conversation | null;
  messages: Message[];
  isStreaming: boolean;
  selectedModel: string;
  availableModels: ModelInfo[];

  setActiveConversation: (conv: Conversation | null) => void;
  addMessage: (msg: Message) => void;
  setMessages: (msgs: Message[]) => void;
  setIsStreaming: (streaming: boolean) => void;
  setSelectedModel: (model: string) => void;
  setAvailableModels: (models: ModelInfo[]) => void;
  setConversations: (convs: Conversation[]) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  activeConversation: null,
  messages: [],
  isStreaming: false,
  selectedModel: "llama3",
  availableModels: [],

  setActiveConversation: (conv) => set({ activeConversation: conv, messages: conv?.messages || [] }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setMessages: (msgs) => set({ messages: msgs }),
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  setSelectedModel: (model) => set({ selectedModel: model }),
  setAvailableModels: (models) => set({ availableModels: models }),
  setConversations: (convs) => set({ conversations: convs }),
}));
