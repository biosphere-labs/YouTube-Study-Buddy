export interface Video {
  id: string;
  videoId: string;
  url: string;
  title?: string;
  transcript?: string;
  processingJob?: ProcessingJob;
  notes: Note[];
  createdAt: string;
}

export interface ProcessingJob {
  id: string;
  videoId: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress: number;
  error?: string;
  result?: any;
  createdAt: string;
  updatedAt: string;
}

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

export interface CreateVideoDto {
  url: string;
  subject?: string;
  generateAssessments?: boolean;
}

export interface Job {
  id: string;
  videoId: string;
  video?: Video;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress: number;
  error?: string;
  result?: any;
  createdAt: string;
  updatedAt: string;
}
