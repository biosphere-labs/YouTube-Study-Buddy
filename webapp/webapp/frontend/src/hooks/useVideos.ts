import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { Video, CreateVideoDto } from '../types';

export function useVideos() {
  return useQuery({
    queryKey: ['videos'],
    queryFn: () => api.get<Video[]>('/videos').then(res => res.data),
  });
}

export function useVideo(id: string) {
  return useQuery({
    queryKey: ['videos', id],
    queryFn: () => api.get<Video>(`/videos/${id}`).then(res => res.data),
    enabled: !!id,
  });
}

export function useCreateVideo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateVideoDto) =>
      api.post<Video>('/videos', data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useDeleteVideo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/videos/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}
