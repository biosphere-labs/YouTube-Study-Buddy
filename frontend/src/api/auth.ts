import apiClient from './client';
import type { AuthResponse, User } from '@/types';

export const authApi = {
  // Initialize OAuth flow
  loginWithGoogle: () => {
    window.location.href = `${apiClient.defaults.baseURL}/auth/google`;
  },

  loginWithGitHub: () => {
    window.location.href = `${apiClient.defaults.baseURL}/auth/github`;
  },

  loginWithDiscord: () => {
    window.location.href = `${apiClient.defaults.baseURL}/auth/discord`;
  },

  // Handle OAuth callback
  handleCallback: async (code: string, provider: string): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>(`/auth/${provider}/callback`, {
      code,
    });
    return response.data;
  },

  // Get current user
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  // Logout
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  },
};
