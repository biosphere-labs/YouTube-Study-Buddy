import { AppLayout } from '@/components/layout/AppLayout';
import { useVideos } from '../hooks/useVideos';
import { useJobSocket } from '../hooks/useJobSocket';
import { VideoSubmitForm } from '../components/videos/VideoSubmitForm';
import { VideoCard } from '../components/videos/VideoCard';
import { JobQueue } from '../components/jobs/JobQueue';
import type { Video } from '../types';

export function Videos() {
  const { data: videos, isLoading, error } = useVideos();
  const { isConnected } = useJobSocket();

  const handleVideoClick = (video: Video) => {
    // Navigate to video details page
    window.location.href = `/videos/${video.id}`;
  };

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight">Videos</h1>
            <p className="text-gray-600 mt-2">
              Submit and manage your YouTube videos
            </p>
          </div>
          {/* Connection Status Indicator */}
          <div className="flex items-center gap-2 text-sm">
            <div
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className={isConnected ? 'text-green-700' : 'text-red-700'}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Video Submit Form */}
        <VideoSubmitForm />

        {/* Job Queue */}
        <JobQueue />

        {/* Videos List */}
        <div>
          <h2 className="text-2xl font-bold mb-4">My Videos</h2>

          {isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse">
                  <div className="bg-gray-200 h-48 rounded-t-lg"></div>
                  <div className="bg-white p-4 rounded-b-lg space-y-3">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
              <p className="text-red-700 font-medium">Failed to load videos</p>
              <p className="text-red-600 text-sm mt-1">
                Please try refreshing the page
              </p>
            </div>
          )}

          {!isLoading && !error && videos && videos.length === 0 && (
            <div className="bg-gray-50 rounded-lg p-12 text-center">
              <svg
                className="w-16 h-16 mx-auto mb-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No videos yet
              </h3>
              <p className="text-gray-600">
                Submit your first YouTube video to get started
              </p>
            </div>
          )}

          {!isLoading && !error && videos && videos.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {videos.map((video) => (
                <VideoCard key={video.id} video={video} onClick={handleVideoClick} />
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
