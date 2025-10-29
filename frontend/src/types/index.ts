export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  provider: 'google' | 'github' | 'discord';
  createdAt: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface Video {
  id: string;
  url: string;
  title: string;
  subject?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  noteId?: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
  error?: string;
}

export interface Note {
  id: string;
  videoId: string;
  title: string;
  content: string;
  subject?: string;
  tags: string[];
  crossReferences: string[];
  userId: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreditBalance {
  userId: string;
  balance: number;
  totalEarned: number;
  totalSpent: number;
}

export interface CreditTransaction {
  id: string;
  userId: string;
  amount: number;
  type: 'purchase' | 'video_processing' | 'refund';
  description: string;
  createdAt: string;
}

export interface UsageStats {
  videosProcessedThisMonth: number;
  totalVideosProcessed: number;
  creditsUsedThisMonth: number;
  totalCreditsUsed: number;
}

export interface WebSocketMessage {
  type: 'progress' | 'completed' | 'error';
  videoId: string;
  progress?: number;
  noteId?: string;
  error?: string;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}
