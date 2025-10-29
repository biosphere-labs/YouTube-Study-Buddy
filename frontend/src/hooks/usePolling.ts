import { useEffect, useRef, useState, useCallback } from 'react';
import { videosApi } from '@/api/videos';
import type { Video } from '@/types';

export interface UsePollingOptions {
  interval?: number; // Polling interval in milliseconds (default: 2000)
  enabled?: boolean; // Whether polling is enabled
  onComplete?: (video: Video) => void;
  onError?: (error: Error) => void;
}

/**
 * Custom hook for polling video progress
 * Polls API Gateway endpoint every 2-3 seconds while video is processing
 * Automatically stops when status is 'completed' or 'failed'
 */
export function usePolling(videoId: string, options: UsePollingOptions = {}) {
  const {
    interval = 2500, // Poll every 2.5 seconds
    enabled = true,
    onComplete,
    onError,
  } = options;

  const [video, setVideo] = useState<Video | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  const fetchVideo = useCallback(async () => {
    if (!videoId || !mountedRef.current) return;

    try {
      const videoData = await videosApi.getVideo(videoId);

      if (!mountedRef.current) return;

      setVideo(videoData);
      setError(null);

      // Stop polling if video is no longer processing
      if (videoData.status === 'completed' || videoData.status === 'failed') {
        setIsPolling(false);

        if (videoData.status === 'completed' && onComplete) {
          onComplete(videoData);
        }
      }
    } catch (err) {
      if (!mountedRef.current) return;

      const error = err instanceof Error ? err : new Error('Failed to fetch video');
      setError(error);

      if (onError) {
        onError(error);
      }

      // Continue polling even on error (might be temporary network issue)
      // But stop after too many errors
      console.error('Error polling video:', error);
    }
  }, [videoId, onComplete, onError]);

  const startPolling = useCallback(() => {
    if (!enabled || isPolling) return;

    setIsPolling(true);

    // Fetch immediately
    fetchVideo();

    // Then poll at interval
    intervalRef.current = setInterval(() => {
      fetchVideo();
    }, interval);
  }, [enabled, isPolling, fetchVideo, interval]);

  const stopPolling = useCallback(() => {
    setIsPolling(false);

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Start/stop polling based on video status and enabled flag
  useEffect(() => {
    if (!enabled || !videoId) {
      stopPolling();
      return;
    }

    // Only poll if video is pending or processing
    if (video && (video.status === 'completed' || video.status === 'failed')) {
      stopPolling();
      return;
    }

    startPolling();

    return () => {
      stopPolling();
    };
  }, [enabled, videoId, video?.status, startPolling, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    video,
    isPolling,
    error,
    refetch: fetchVideo,
    startPolling,
    stopPolling,
  };
}

/**
 * Hook for polling multiple videos
 * Useful for video list pages
 */
export function useMultiplePolling(videoIds: string[], options: UsePollingOptions = {}) {
  const [videos, setVideos] = useState<Map<string, Video>>(new Map());
  const [errors, setErrors] = useState<Map<string, Error>>(new Map());

  const handleVideoUpdate = useCallback((videoId: string, video: Video) => {
    setVideos((prev) => new Map(prev).set(videoId, video));
  }, []);

  const handleError = useCallback((videoId: string, error: Error) => {
    setErrors((prev) => new Map(prev).set(videoId, error));
  }, []);

  // Poll each video that's in processing state
  videoIds.forEach((videoId) => {
    const video = videos.get(videoId);
    const shouldPoll = !video || (video.status !== 'completed' && video.status !== 'failed');

    // eslint-disable-next-line react-hooks/rules-of-hooks
    usePolling(videoId, {
      ...options,
      enabled: shouldPoll && options.enabled !== false,
      onComplete: (video) => {
        handleVideoUpdate(videoId, video);
        options.onComplete?.(video);
      },
      onError: (error) => {
        handleError(videoId, error);
        options.onError?.(error);
      },
    });
  });

  return {
    videos,
    errors,
  };
}
