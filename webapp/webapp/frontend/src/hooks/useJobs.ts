import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { Job } from '../types';

export function useJobs() {
  return useQuery({
    queryKey: ['jobs'],
    queryFn: () => api.get<Job[]>('/jobs').then(res => res.data),
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ['jobs', id],
    queryFn: () => api.get<Job>(`/jobs/${id}`).then(res => res.data),
    enabled: !!id,
  });
}

export function useRetryJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post(`/jobs/${id}/retry`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });
}

export function useCancelJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/jobs/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });
}
