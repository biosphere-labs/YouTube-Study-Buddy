import React from 'react';
import type { Video } from '../../types';
import { JobStatusBadge } from '../jobs/JobStatusBadge';
import { JobProgressBar } from '../jobs/JobProgressBar';
import { useDeleteVideo } from '../../hooks/useVideos';
import { toast } from 'sonner';

interface VideoCardProps {
  video: Video;
  onClick?: (video: Video) => void;
}

// Extract YouTube video ID from URL
function extractVideoId(url: string): string | null {
  const patterns = [
    /youtube\.com\/watch\?v=([^&]+)/,
    /youtu\.be\/([^?]+)/,
    /youtube\.com\/embed\/([^?]+)/,
  ];

  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return null;
}

export const VideoCard: React.FC<VideoCardProps> = ({ video, onClick }) => {
  const deleteVideo = useDeleteVideo();
  const videoId = extractVideoId(video.url);
  const thumbnailUrl = videoId
    ? `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`
    : null;

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this video and its notes?')) {
      return;
    }

    try {
      await deleteVideo.mutateAsync(video.id);
      toast.success('Video deleted successfully');
    } catch (error) {
      toast.error('Failed to delete video');
      console.error('Delete error:', error);
    }
  };

  const handleCardClick = () => {
    if (onClick) onClick(video);
  };

  const job = video.processingJob;
  const notesCount = video.notes?.length || 0;

  return (
    <div
      onClick={handleCardClick}
      className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer overflow-hidden"
    >
      {/* Thumbnail */}
      {thumbnailUrl ? (
        <img
          src={thumbnailUrl}
          alt={video.title || 'Video thumbnail'}
          className="w-full h-48 object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="320" height="180"%3E%3Crect fill="%23ddd" width="320" height="180"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle"%3ENo Thumbnail%3C/text%3E%3C/svg%3E';
          }}
        />
      ) : (
        <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
          <span className="text-gray-400">No Thumbnail</span>
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        {/* Title */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
          {video.title || 'Untitled Video'}
        </h3>

        {/* URL */}
        <p className="text-sm text-gray-500 mb-3 truncate">{video.url}</p>

        {/* Status Badge */}
        {job && (
          <div className="mb-3">
            <JobStatusBadge status={job.status} />
          </div>
        )}

        {/* Progress Bar (if processing) */}
        {job && job.status === 'PROCESSING' && (
          <div className="mb-3">
            <JobProgressBar progress={job.progress} status={job.status} />
          </div>
        )}

        {/* Error Message (if failed) */}
        {job && job.status === 'FAILED' && job.error && (
          <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            {job.error}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-200">
          {/* Notes count */}
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span className="inline-flex items-center gap-1">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              {notesCount} {notesCount === 1 ? 'note' : 'notes'}
            </span>
          </div>

          {/* Delete button */}
          <button
            onClick={handleDelete}
            disabled={deleteVideo.isPending}
            className="text-red-600 hover:text-red-800 text-sm font-medium disabled:opacity-50"
          >
            {deleteVideo.isPending ? 'Deleting...' : 'Delete'}
          </button>
        </div>

        {/* Created date */}
        <div className="mt-2 text-xs text-gray-400">
          {new Date(video.createdAt).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })}
        </div>
      </div>
    </div>
  );
};
