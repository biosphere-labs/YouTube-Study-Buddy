import { useQuery } from '@tanstack/react-query';
import { authApi } from '@/lib/auth';
import { useAuthStore } from '@/stores/authStore';

export function useUser() {
  const token = useAuthStore((state) => state.token);

  return useQuery({
    queryKey: ['user'],
    queryFn: () => authApi.getCurrentUser(),
    enabled: !!token,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
