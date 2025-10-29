import { useAuthStore } from '@/stores/authStore';
import { authApi } from '@/api/auth';
import { useMutation, useQuery } from '@tanstack/react-query';
import type { AuthResponse } from '@/types';

export function useAuth() {
  const { user, token, isAuthenticated, setAuth, clearAuth } = useAuthStore();

  // Query to get current user
  const { data: currentUser, isLoading } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    enabled: !!token && !user,
    retry: false,
  });

  // Mutation for logout
  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      clearAuth();
    },
  });

  const login = (authResponse: AuthResponse) => {
    setAuth(authResponse.user, authResponse.token);
  };

  const logout = () => {
    logoutMutation.mutate();
  };

  return {
    user: user || currentUser,
    isAuthenticated,
    isLoading,
    login,
    logout,
    loginWithGoogle: authApi.loginWithGoogle,
    loginWithGitHub: authApi.loginWithGitHub,
    loginWithDiscord: authApi.loginWithDiscord,
  };
}
