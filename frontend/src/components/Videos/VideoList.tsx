import { useQuery } from '@tanstack/react-query';
import { VideoCard } from './VideoCard';
import { VideoSubmit } from './VideoSubmit';
import { videosApi } from '@/api/videos';
import { Loader2 } from 'lucide-react';

export function VideoList() {
  const { data: videos, isLoading, error } = useQuery({
    queryKey: ['videos'],
    queryFn: videosApi.getVideos,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md">
        <p className="text-destructive">Failed to load videos. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Videos</h1>
        <p className="text-muted-foreground">
          Submit and manage your YouTube videos
        </p>
      </div>

      <VideoSubmit />

      {videos && videos.length > 0 ? (
        <div>
          <h2 className="text-xl font-semibold mb-4">Your Videos</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {videos.map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            No videos yet. Submit your first video above!
          </p>
        </div>
      )}
    </div>
  );
}
