import { create } from "zustand";
import api from "@/lib/api";
import { setTokens, clearTokens } from "@/lib/auth";
import { supabase } from "@/lib/supabase";
import type { User, TokenResponse } from "@/types/auth";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<{ needsVerification: boolean }>;
  verifyOtp: (email: string, token: string, fullName: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  setUser: (user: User | null) => void;
}

async function syncWithBackend(email: string, password: string, fullName?: string): Promise<void> {
  try {
    const res = await api.post<TokenResponse>("/auth/login", { email, password });
    setTokens(res.data.access_token, res.data.refresh_token);
  } catch (loginErr: unknown) {
    const err = loginErr as { response?: { status?: number } };
    if (err.response?.status === 401 && fullName) {
      const res = await api.post<TokenResponse>("/auth/register", {
        email,
        password,
        full_name: fullName,
      });
      setTokens(res.data.access_token, res.data.refresh_token);
    } else {
      throw loginErr;
    }
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw new Error(error.message);
      if (!data.user) throw new Error("Login failed. Please try again.");

      await syncWithBackend(email, password);

      const userRes = await api.get<User>("/auth/me");
      set({ user: userRes.data, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  register: async (email: string, password: string, fullName: string) => {
    set({ isLoading: true });
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { full_name: fullName } },
      });

      if (error) throw new Error(error.message);

      if (data.session) {
        await syncWithBackend(email, password, fullName);
        const userRes = await api.get<User>("/auth/me");
        set({ user: userRes.data, isAuthenticated: true, isLoading: false });
        return { needsVerification: false };
      }

      set({ isLoading: false });
      return { needsVerification: true };
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  verifyOtp: async (email: string, token: string, fullName: string, password: string) => {
    set({ isLoading: true });
    try {
      const { data, error } = await supabase.auth.verifyOtp({
        email,
        token,
        type: "signup",
      });

      if (error) throw new Error(error.message);
      if (!data.session) throw new Error("OTP verification failed. Please try again.");

      await syncWithBackend(email, password, fullName);

      const userRes = await api.get<User>("/auth/me");
      set({ user: userRes.data, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    supabase.auth.signOut().catch(() => { });
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