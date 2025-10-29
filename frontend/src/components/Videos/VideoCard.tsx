import { Link } from 'react-router-dom';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ProgressBar } from './ProgressBar';
import type { Video } from '@/types';
import { FileText, Trash2, RefreshCw } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { videosApi } from '@/api/videos';
import { usePolling } from '@/hooks/usePolling';

interface VideoCardProps {
  video: Video;
}

export function VideoCard({ video: initialVideo }: VideoCardProps) {
  const queryClient = useQueryClient();

  // Use polling hook to track video progress
  const { video: polledVideo } = usePolling(initialVideo.id, {
    enabled: initialVideo.status === 'pending' || initialVideo.status === 'processing',
    onComplete: () => {
      // Refresh video list when processing completes
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
    onError: (error) => {
      console.error('Error polling video:', error);
    },
  });

  // Use polled video if available, otherwise use initial video
  const video = polledVideo || initialVideo;

  const deleteMutation = useMutation({
    mutationFn: () => videosApi.deleteVideo(video.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });

  const retryMutation = useMutation({
    mutationFn: () => videosApi.retryVideo(video.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg line-clamp-2">{video.title}</CardTitle>
        {video.subject && (
          <p className="text-sm text-muted-foreground">Subject: {video.subject}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        <ProgressBar progress={video.progress} status={video.status} />

        {video.error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
            <p className="text-sm text-destructive">{video.error}</p>
          </div>
        )}

        <p className="text-sm text-muted-foreground">
          Created: {new Date(video.createdAt).toLocaleString()}
        </p>
      </CardContent>
      <CardFooter className="flex gap-2">
        {video.status === 'completed' && video.noteId && (
          <Link to={`/notes/${video.noteId}`} className="flex-1">
            <Button variant="default" className="w-full">
              <FileText className="mr-2 h-4 w-4" />
              View Note
            </Button>
          </Link>
        )}

        {video.status === 'failed' && (
          <Button
            variant="outline"
            onClick={() => retryMutation.mutate()}
            disabled={retryMutation.isPending}
            className="flex-1"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        )}

        <Button
          variant="destructive"
          size="icon"
          onClick={() => {
            if (confirm('Are you sure you want to delete this video?')) {
              deleteMutation.mutate();
            }
          }}
          disabled={deleteMutation.isPending}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}
