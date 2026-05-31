import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Auth API (through nginx: /api/v1/* -> auth:8001)
export const authApi = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Content API (through nginx: /api/v1/content/* -> content:8002)
export const contentApi = axios.create({
  baseURL: `${baseURL}/content`,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Assessment API (through nginx: /api/v1/tests, /api/v1/questions, /api/v1/attempts -> assessment:8003)
export const assessmentApi = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Refresh token handling ──
let isRefreshing = false;
let refreshSubscribers: Array<(error: AxiosError | null) => void> = [];

function onRefreshed(error: AxiosError | null) {
  refreshSubscribers.forEach((cb) => cb(error));
  refreshSubscribers = [];
}

function addRefreshSubscriber(callback: (error: AxiosError | null) => void) {
  refreshSubscribers.push(callback);
}

function redirectToLogin() {
  const isAuthPage = ['/login', '/register'].includes(window.location.pathname);
  if (!isAuthPage) {
    window.location.href = '/login';
  }
}

async function handleAuthError(error: AxiosError, axiosInstance: AxiosInstance) {
  const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

  // If the failed request was the refresh itself, don't loop
  if (originalRequest.url?.includes('/auth/refresh')) {
    redirectToLogin();
    return Promise.reject(error);
  }

  if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        addRefreshSubscriber((err) => {
          if (err) reject(err);
          else resolve(axiosInstance(originalRequest));
        });
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      await authApi.post('/auth/refresh');
      onRefreshed(null);
      return axiosInstance(originalRequest);
    } catch (refreshErr: any) {
      onRefreshed(refreshErr);
      redirectToLogin();
      return Promise.reject(refreshErr);
    } finally {
      isRefreshing = false;
    }
  }

  return Promise.reject(error);
}

authApi.interceptors.response.use(
  (res) => res,
  (err) => handleAuthError(err, authApi)
);
contentApi.interceptors.response.use(
  (res) => res,
  (err) => handleAuthError(err, contentApi)
);
assessmentApi.interceptors.response.use(
  (res) => res,
  (err) => handleAuthError(err, assessmentApi)
);
