import { create } from "zustand";
import api from "@/lib/api";
import { setTokens, clearTokens } from "@/lib/auth";
import type { User, LoginRequest, RegisterRequest, TokenResponse } from "@/types/auth";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  isAuthenticated: false,

  login: async (data: LoginRequest) => {
    set({ isLoading: true });
    try {
      const res = await api.post<TokenResponse>("/auth/login", data);
      setTokens(res.data.access_token, res.data.refresh_token);

      const userRes = await api.get<User>("/auth/me");
      set({ user: userRes.data, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  register: async (data: RegisterRequest) => {
    set({ isLoading: true });
    try {
      const res = await api.post<TokenResponse>("/auth/register", data);
      setTokens(res.data.access_token, res.data.refresh_token);

      const userRes = await api.get<User>("/auth/me");
      set({ user: userRes.data, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    clearTokens();
    set({ user: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    set({ isLoading: true });
    try {
      const res = await api.get<User>("/auth/me");
      set({ user: res.data, isAuthenticated: true, isLoading: false });
    } catch {
      clearTokens();
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  setUser: (user) => set({ user, isAuthenticated: !!user }),
}));
