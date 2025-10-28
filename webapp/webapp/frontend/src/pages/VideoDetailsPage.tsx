import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { useVideo } from '../hooks/useVideos';
import { useRetryJob } from '../hooks/useJobs';
import { useJobSocket } from '../hooks/useJobSocket';
import { JobStatusBadge } from '../components/jobs/JobStatusBadge';
import { JobProgressBar } from '../components/jobs/JobProgressBar';
import { toast } from 'sonner';

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

export function VideoDetailsPage() {
  const params = useParams<{ id: string }>();
  const id = params.id || '';
  const navigate = useNavigate();
  const videoResult = useVideo(id);
  const video = videoResult.data;
  const isLoading = videoResult.isLoading;
  const error = videoResult.error;
  const retryJob = useRetryJob();
  const socketResult = useJobSocket();
  const isConnected = socketResult.isConnected;

  const handleRetry = async () => {
    if (!video?.processingJob) return;

    try {
      await retryJob.mutateAsync(video.processingJob.id);
      toast.success('Job restarted');
    } catch (error) {
      toast.error('Failed to retry job');
      console.error('Retry error:', error);
    }
  };

  const handleBack = () => {
    navigate('/videos');
  };

  const handleNoteClick = (noteId: string) => {
    navigate(`/notes/${noteId}`);
  };

  if (isLoading) {
    return (
      <AppLayout>
        <div className="space-y-6 animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </AppLayout>
    );
  }

  if (error || !video) {
    return (
      <AppLayout>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-700 font-medium">Failed to load video</p>
          <button
            onClick={handleBack}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Back to Videos
          </button>
        </div>
      </AppLayout>
    );
  }

  const videoId = extractVideoId(video.url);
  const embedUrl = videoId ? `https://www.youtube.com/embed/${videoId}` : null;
  const job = video.processingJob;

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header with back button */}
        <div className="flex items-center gap-4">
          <button
            onClick={handleBack}
            className="text-gray-600 hover:text-gray-900 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
          </button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold">{video.title || 'Video Details'}</h1>
          </div>
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

        {/* Video Player */}
        {embedUrl && (
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="aspect-video">
              <iframe
                src={embedUrl}
                title={video.title || 'YouTube video'}
                className="w-full h-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          </div>
        )}

        {/* Video Information */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4">Video Information</h2>
          <div className="space-y-3">
            <div>
              <span className="text-sm font-medium text-gray-600">URL:</span>
              <a
                href={video.url}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-2 text-blue-600 hover:underline"
              >
                {video.url}
              </a>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Created:</span>
              <span className="ml-2 text-gray-900">
                {new Date(video.createdAt).toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* Processing Job Status */}
        {job && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Processing Status</h2>
              <JobStatusBadge status={job.status} />
            </div>

            {(job.status === 'QUEUED' || job.status === 'PROCESSING') && (
              <JobProgressBar progress={job.progress} status={job.status} />
            )}

            {job.status === 'FAILED' && (
              <div>
                <div className="p-4 bg-red-50 border border-red-200 rounded mb-4">
                  <p className="text-red-700 font-medium">Processing Failed</p>
                  {job.error && (
                    <p className="text-red-600 text-sm mt-1">{job.error}</p>
                  )}
                </div>
                <button
                  onClick={handleRetry}
                  disabled={retryJob.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  {retryJob.isPending ? 'Retrying...' : 'Retry Processing'}
                </button>
              </div>
            )}

            {job.status === 'COMPLETED' && (
              <div className="p-4 bg-green-50 border border-green-200 rounded">
                <p className="text-green-700 font-medium">Processing Completed!</p>
                <p className="text-green-600 text-sm mt-1">
                  Your study notes are ready below
                </p>
              </div>
            )}
          </div>
        )}

        {/* Generated Notes */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4">
            Generated Notes ({video.notes?.length || 0})
          </h2>

          {video.notes && video.notes.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <svg
                className="w-12 h-12 mx-auto mb-3 text-gray-400"
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
              <p className="font-medium">No notes generated yet</p>
              <p className="text-sm">
                {job?.status === 'PROCESSING'
                  ? 'Processing is in progress...'
                  : job?.status === 'QUEUED'
                  ? 'Waiting in queue...'
                  : 'Submit the video for processing'}
              </p>
            </div>
          )}

          {video.notes && video.notes.length > 0 && (
            <div className="grid gap-4">
              {video.notes.map((note) => (
                <div
                  key={note.id}
                  onClick={() => handleNoteClick(note.id)}
                  className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
                >
                  <h3 className="font-semibold text-lg mb-2">{note.title}</h3>
                  {note.subject && (
                    <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium mb-2">
                      {note.subject}
                    </span>
                  )}
                  <p className="text-gray-600 text-sm line-clamp-3">
                    {note.content.substring(0, 200)}...
                  </p>
                  <div className="mt-3 text-xs text-gray-400">
                    {new Date(note.createdAt).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
