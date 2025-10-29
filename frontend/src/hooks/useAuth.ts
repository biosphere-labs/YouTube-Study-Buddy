import { useAuthStore } from '@/stores/authStore';
import { authApi } from '@/api/auth';
import { useMutation } from '@tanstack/react-query';

export function useAuth() {
  const { user, isAuthenticated, isLoading, clearAuth } = useAuthStore();

  // Mutation for logout
  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      clearAuth();
    },
  });

  const logout = () => {
    logoutMutation.mutate();
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    logout,
    loginWithGoogle: authApi.loginWithGoogle,
    loginWithGitHub: authApi.loginWithGitHub,
    loginWithDiscord: authApi.loginWithDiscord,
  };
}
