import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

/**
 * Configured axios instance with auth interceptors.
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Accept": "application/json",
  },
  timeout: 120000,
});

// ── Request Interceptor: Attach JWT ─────────────────────
api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response Interceptor: Handle 401 ────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);

          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return api(originalRequest);
        }
      } catch {
        // Refresh failed — clear tokens and redirect to login
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;
