import apiClient from './client';
import type { Note } from '@/types';

export interface UpdateNoteRequest {
  content?: string;
  subject?: string;
  tags?: string[];
}

export interface ListNotesResponse {
  notes: Note[];
  nextToken?: string;
}

export const notesApi = {
  // Get all notes for current user with pagination support
  getNotes: async (limit: number = 50, nextToken?: string): Promise<ListNotesResponse> => {
    const params: Record<string, string | number> = { limit };
    if (nextToken) {
      params.nextToken = nextToken;
    }
    const response = await apiClient.get<ListNotesResponse>('/notes', { params });
    return response.data;
  },

  // Get a specific note by ID
  getNote: async (id: string): Promise<Note> => {
    const response = await apiClient.get<Note>(`/notes/${id}`);
    return response.data;
  },

  // Update a note (using PUT as per serverless standards)
  updateNote: async (id: string, data: UpdateNoteRequest): Promise<Note> => {
    const response = await apiClient.put<Note>(`/notes/${id}`, data);
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
