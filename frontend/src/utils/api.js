/**
 * Axios instance — all API calls go through this.
 * - Injects Authorization header automatically from authStore
 * - On 401: clears tokens + redirects to /login
 * - On 403: dispatches toast event (handled in App.jsx)
 */
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — attach JWT
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — handle 401 / 403
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;

    if (status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }

    if (status === 403) {
      window.dispatchEvent(
        new CustomEvent('dms:forbidden', {
          detail: error.response?.data?.detail || 'You do not have permission for this action',
        })
      );
    }

    return Promise.reject(error);
  }
);

export default api;
