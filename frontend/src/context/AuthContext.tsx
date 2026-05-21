import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { authApi } from '../api/client';
import type { Token, User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (roles: string[]) => boolean;
  updateUser: (data: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function decodeToken(token: string): any {
  try {
    const base64 = token.split('.')[1];
    const json = atob(base64.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

async function tryRefreshToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) return null;

  try {
    const res = await axios.post('/api/v1/auth/refresh', null, {
      params: { refresh_token: refreshToken },
    });
    const { access_token, refresh_token } = res.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    return access_token;
  } catch {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        const payload = decodeToken(token);
        const isExpired = !payload || payload.exp * 1000 <= Date.now();

        if (isExpired) {
          const newToken = await tryRefreshToken();
          if (!newToken) {
            setIsLoading(false);
            return;
          }
        }

        try {
          const res = await authApi.get('/users/me');
          setUser(res.data);
        } catch {
          // Interceptor will handle redirect if refresh also failed
        } finally {
          setIsLoading(false);
        }
      } else {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const res = await authApi.post<Token>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const { access_token, refresh_token } = res.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    const userRes = await authApi.get('/users/me');
    setUser(userRes.data);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.post('/auth/logout');
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
    }
  }, []);

  const hasRole = useCallback((roles: string[]) => {
    return user ? roles.includes(user.role) : false;
  }, [user]);

  const updateUser = useCallback((data: Partial<User>) => {
    setUser((prev) => (prev ? { ...prev, ...data } : prev));
  }, []);

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      logout,
      hasRole,
      updateUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
