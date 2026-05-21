import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:80';

// Auth API (через nginx: /api/v1/* → auth:8001)
export const authApi = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Content API (через nginx: /api/v1/content/* → content:8002)
export const contentApi = axios.create({
  baseURL: `${API_BASE}/api/v1/content`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor для добавления токена
const addToken = (config: any) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

authApi.interceptors.request.use(addToken);
contentApi.interceptors.request.use(addToken);

// Interceptor для обработки 401
const handleAuthError = (error: any) => {
  if (error.response?.status === 401) {
    const isAuthPage = window.location.pathname === '/login' || window.location.pathname === '/register';
    if (!isAuthPage) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
  }
  return Promise.reject(error);
};

authApi.interceptors.response.use((res) => res, handleAuthError);
contentApi.interceptors.response.use((res) => res, handleAuthError);
