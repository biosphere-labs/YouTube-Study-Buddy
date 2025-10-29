import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';
import { getCognitoUser, getIdToken } from '@/lib/cognito';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  setIsAuthenticated: (isAuthenticated: boolean) => void;
  setIsLoading: (isLoading: boolean) => void;
  clearAuth: () => void;
  initAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,

      setUser: (user) => {
        set({ user, isAuthenticated: !!user });
      },

      setIsAuthenticated: (isAuthenticated) => {
        set({ isAuthenticated });
      },

      setIsLoading: (isLoading) => {
        set({ isLoading });
      },

      clearAuth: () => {
        set({ user: null, isAuthenticated: false });
      },

      // Initialize auth state from Cognito
      initAuth: async () => {
        try {
          set({ isLoading: true });

          // Check if user has valid Cognito session
          const token = await getIdToken();
          if (!token) {
            set({ user: null, isAuthenticated: false, isLoading: false });
            return;
          }

          // Get user data from Cognito
          const user = await getCognitoUser();
          if (user) {
            set({ user, isAuthenticated: true, isLoading: false });
          } else {
            set({ user: null, isAuthenticated: false, isLoading: false });
          }
        } catch (error) {
          console.error('Error initializing auth:', error);
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
