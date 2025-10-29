import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { Video as VideoType } from '@/types';
import { Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface RecentVideosProps {
  videos: VideoType[];
}

export function RecentVideos({ videos }: RecentVideosProps) {
  const getStatusIcon = (status: VideoType['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'processing':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  if (videos.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Videos</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No videos yet. Submit your first YouTube video to get started!
          </p>
          <div className="flex justify-center">
            <Link to="/videos">
              <Button>Submit Video</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Videos</CardTitle>
        <Link to="/videos">
          <Button variant="outline" size="sm">
            View All
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {videos.map((video) => (
            <div
              key={video.id}
              className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent transition-colors"
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                {getStatusIcon(video.status)}
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{video.title}</p>
                  <p className="text-sm text-muted-foreground">
                    {new Date(video.createdAt).toLocaleDateString()}
                  </p>
                </div>
              </div>
              {video.noteId && (
                <Link to={`/notes/${video.noteId}`}>
                  <Button variant="ghost" size="sm">
                    View Note
                  </Button>
                </Link>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
