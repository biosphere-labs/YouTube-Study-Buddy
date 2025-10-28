import { create } from 'zustand';
import type { User } from '@/types/auth';
import { authApi, setAuthToken, removeAuthToken } from '@/lib/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('auth_token'),
  isAuthenticated: false,
  isLoading: true,

  login: async (token: string) => {
    try {
      setAuthToken(token);
      set({ token });

      // Fetch user data
      const user = await authApi.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });

      // Store user in localStorage for persistence
      localStorage.setItem('user', JSON.stringify(user));
    } catch (error) {
      console.error('Login failed:', error);
      removeAuthToken();
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      removeAuthToken();
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },

  checkAuth: async () => {
    const token = localStorage.getItem('auth_token');

    if (!token) {
      set({ isLoading: false, isAuthenticated: false });
      return;
    }

    try {
      const user = await authApi.getCurrentUser();
      set({ user, token, isAuthenticated: true, isLoading: false });
      localStorage.setItem('user', JSON.stringify(user));
    } catch (error) {
      console.error('Auth check failed:', error);
      removeAuthToken();
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },

  setUser: (user: User) => {
    set({ user });
    localStorage.setItem('user', JSON.stringify(user));
  },
}));
