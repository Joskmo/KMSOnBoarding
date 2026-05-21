import axios from 'axios';

// Dev: Vite proxy intercepts /api → localhost:80
// Prod: nginx on the same origin handles /api
const baseURL = '/api/v1';

// Auth API (through nginx: /api/v1/* → auth:8001)
export const authApi = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Content API (through nginx: /api/v1/content/* → content:8002)
export const contentApi = axios.create({
  baseURL: `${baseURL}/content`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Assessment API (through nginx: /api/v1/tests, /api/v1/questions, /api/v1/attempts → assessment:8003)
export const assessmentApi = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor for adding token
const addToken = (config: any) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

authApi.interceptors.request.use(addToken);
contentApi.interceptors.request.use(addToken);
assessmentApi.interceptors.request.use(addToken);

// Interceptor for handling 401
const handleAuthError = (error: any) => {
  if (error.response?.status === 401) {
    const isAuthPage = ['/login', '/register'].includes(window.location.pathname);
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
assessmentApi.interceptors.response.use((res) => res, handleAuthError);
