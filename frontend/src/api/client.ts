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

// Separate instance for refresh to avoid interceptor recursion
const refreshApi = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback);
}

function onTokenRefreshed(newToken: string) {
  refreshSubscribers.forEach((callback) => callback(newToken));
  refreshSubscribers = [];
}

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

// Helper to refresh token
async function doRefresh() {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    throw new Error('No refresh token');
  }
  const res = await refreshApi.post('/auth/refresh', { refresh_token: refreshToken });
  const { access_token, refresh_token } = res.data;
  localStorage.setItem('access_token', access_token);
  localStorage.setItem('refresh_token', refresh_token);
  return access_token;
}

// Interceptor for handling 401
function createAuthErrorInterceptor(api: any) {
  return async (error: any) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      // Don't try to refresh if this is the refresh request itself
      if (originalRequest.url?.includes('/auth/refresh')) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Wait for refresh to complete, then retry
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken: string) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newToken = await doRefresh();
        onTokenRefreshed(newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        const isAuthPage = ['/login', '/register'].includes(window.location.pathname);
        if (!isAuthPage) {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  };
}

authApi.interceptors.response.use(
  (res) => res,
  createAuthErrorInterceptor(authApi)
);
contentApi.interceptors.response.use(
  (res) => res,
  createAuthErrorInterceptor(contentApi)
);
assessmentApi.interceptors.response.use(
  (res) => res,
  createAuthErrorInterceptor(assessmentApi)
);
