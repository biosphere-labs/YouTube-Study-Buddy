import apiClient from './client';
import type { Video } from '@/types';

export interface SubmitVideoRequest {
  url: string;
  subject?: string;
}

export const videosApi = {
  // Submit a new video for processing
  submitVideo: async (data: SubmitVideoRequest): Promise<Video> => {
    const response = await apiClient.post<Video>('/videos', data);
    return response.data;
  },

  // Get all videos for current user
  getVideos: async (): Promise<Video[]> => {
    const response = await apiClient.get<Video[]>('/videos');
    return response.data;
  },

  // Get a specific video by ID
  getVideo: async (id: string): Promise<Video> => {
    const response = await apiClient.get<Video>(`/videos/${id}`);
    return response.data;
  },

  // Delete a video
  deleteVideo: async (id: string): Promise<void> => {
    await apiClient.delete(`/videos/${id}`);
  },

  // Retry failed video processing
  retryVideo: async (id: string): Promise<Video> => {
    const response = await apiClient.post<Video>(`/videos/${id}/retry`);
    return response.data;
  },
};
