import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Note, PaginatedNotes, NotesQuery, UpdateNoteDto } from '../types/note';

export function useNotes(query?: NotesQuery) {
  return useQuery({
    queryKey: ['notes', query],
    queryFn: async () => {
      const response = await api.get<PaginatedNotes>('/notes', { params: query });
      return response.data;
    },
  });
}

export function useNote(id: string) {
  return useQuery({
    queryKey: ['notes', id],
    queryFn: async () => {
      const response = await api.get<Note>(`/notes/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useUpdateNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateNoteDto }) => {
      const response = await api.put<Note>(`/notes/${id}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      // Update the single note cache
      queryClient.setQueryData(['notes', data.id], data);
      // Invalidate the notes list to refetch
      queryClient.invalidateQueries({ queryKey: ['notes'] });
    },
  });
}

export function useDeleteNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/notes/${id}`);
      return id;
    },
    onSuccess: () => {
      // Invalidate the notes list to refetch
      queryClient.invalidateQueries({ queryKey: ['notes'] });
    },
  });
}
