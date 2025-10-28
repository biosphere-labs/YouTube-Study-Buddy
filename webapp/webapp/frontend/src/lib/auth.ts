import { api } from './api';
import type { User, AuthResponse } from '@/types/auth';

export const authApi = {
  // Get current user
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  // Logout
  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  },

  // OAuth redirect URLs
  getOAuthUrl: (provider: 'google' | 'github' | 'discord'): string => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000';
    return `${baseUrl}/auth/${provider}`;
  },

  // Handle OAuth callback
  handleOAuthCallback: async (
    provider: string,
    code: string
  ): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>(`/auth/${provider}/callback`, {
      code,
    });
    return response.data;
  },
};

export const setAuthToken = (token: string): void => {
  localStorage.setItem('auth_token', token);
};

export const getAuthToken = (): string | null => {
  return localStorage.getItem('auth_token');
};

export const removeAuthToken = (): void => {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user');
};
