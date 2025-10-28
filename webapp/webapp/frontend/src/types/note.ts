export interface Note {
  id: string;
  userId: string;
  videoId?: string;
  title: string;
  content: string;
  subject?: string;
  assessmentContent?: string;
  pdfUrl?: string;
  createdAt: string;
  updatedAt: string;
}

export interface UpdateNoteDto {
  title?: string;
  content?: string;
  subject?: string;
}

export interface NotesQuery {
  subject?: string;
  search?: string;
  page?: number;
  limit?: number;
  sortBy?: 'date' | 'title' | 'subject';
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedNotes {
  data: Note[];
  meta: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
