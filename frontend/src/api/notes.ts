import apiClient from './client';
import type { Note } from '@/types';

export interface UpdateNoteRequest {
  content?: string;
  subject?: string;
  tags?: string[];
}

export const notesApi = {
  // Get all notes for current user
  getNotes: async (): Promise<Note[]> => {
    const response = await apiClient.get<Note[]>('/notes');
    return response.data;
  },

  // Get a specific note by ID
  getNote: async (id: string): Promise<Note> => {
    const response = await apiClient.get<Note>(`/notes/${id}`);
    return response.data;
  },

  // Update a note
  updateNote: async (id: string, data: UpdateNoteRequest): Promise<Note> => {
    const response = await apiClient.patch<Note>(`/notes/${id}`, data);
    return response.data;
  },

  // Delete a note
  deleteNote: async (id: string): Promise<void> => {
    await apiClient.delete(`/notes/${id}`);
  },

  // Export note as markdown
  exportNote: async (id: string): Promise<Blob> => {
    const response = await apiClient.get(`/notes/${id}/export`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Search notes
  searchNotes: async (query: string): Promise<Note[]> => {
    const response = await apiClient.get<Note[]>('/notes/search', {
      params: { q: query },
    });
    return response.data;
  },
};
