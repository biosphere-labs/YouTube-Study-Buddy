import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { io, Socket } from 'socket.io-client';
import { toast } from 'sonner';

const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:3000';

export function useJobSocket() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const queryClient = useQueryClient();

  useEffect(() => {
    const token = localStorage.getItem('auth_token');

    const ws = io(WS_URL, {
      auth: { token },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    ws.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      toast.success('Connected to server');
    });

    ws.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      toast.error('Disconnected from server');
    });

    ws.on('job:progress', (data: { jobId: string; progress: number; status?: string }) => {
      console.log('Job progress update:', data);

      // Update job in cache
      queryClient.setQueryData(['jobs', data.jobId], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          progress: data.progress,
          status: data.status || old.status,
        };
      });

      // Invalidate jobs list to refresh
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    });

    ws.on('job:completed', (data: { jobId: string; videoId: string }) => {
      console.log('Job completed:', data);

      // Show success toast
      toast.success('Video processing completed! Notes are ready.');

      // Refetch videos and notes
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['videos', data.videoId] });
      queryClient.invalidateQueries({ queryKey: ['notes'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['jobs', data.jobId] });
    });

    ws.on('job:failed', (data: { jobId: string; error: string }) => {
      console.error('Job failed:', data);

      // Show error toast
      toast.error(`Processing failed: ${data.error}`);

      // Update job with error
      queryClient.setQueryData(['jobs', data.jobId], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          status: 'FAILED',
          error: data.error,
        };
      });

      // Invalidate jobs list
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    });

    ws.on('job:started', (data: { jobId: string; videoId: string }) => {
      console.log('Job started:', data);
      toast.info('Video processing started');
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    });

    setSocket(ws);

    return () => {
      console.log('Cleaning up WebSocket connection');
      ws.disconnect();
    };
  }, [queryClient]);

  return { socket, isConnected };
}
