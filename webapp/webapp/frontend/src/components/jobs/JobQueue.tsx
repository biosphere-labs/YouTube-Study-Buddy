import React, { useState } from 'react';
import { useJobs, useRetryJob, useCancelJob } from '../../hooks/useJobs';
import { JobStatusBadge } from './JobStatusBadge';
import { JobProgressBar } from './JobProgressBar';
import { toast } from 'sonner';

export const JobQueue: React.FC = () => {
  const { data: jobs, isLoading, error } = useJobs();
  const retryJob = useRetryJob();
  const cancelJob = useCancelJob();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleRetry = async (jobId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await retryJob.mutateAsync(jobId);
      toast.success('Job restarted');
    } catch (error) {
      toast.error('Failed to retry job');
      console.error('Retry error:', error);
    }
  };

  const handleCancel = async (jobId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to cancel this job?')) {
      return;
    }

    try {
      await cancelJob.mutateAsync(jobId);
      toast.success('Job cancelled');
    } catch (error) {
      toast.error('Failed to cancel job');
      console.error('Cancel error:', error);
    }
  };

  const getTimeElapsed = (createdAt: string) => {
    const created = new Date(createdAt);
    const now = new Date();
    const diff = now.getTime() - created.getTime();
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);

    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-100 rounded"></div>
            <div className="h-20 bg-gray-100 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-red-600">Failed to load jobs</div>
      </div>
    );
  }

  const activeJobs = jobs?.filter(
    (job) => job.status === 'QUEUED' || job.status === 'PROCESSING'
  ) || [];

  if (activeJobs.length === 0 && isCollapsed) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md">
      {/* Header */}
      <div
        className="p-4 border-b border-gray-200 flex items-center justify-between cursor-pointer"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <h2 className="text-xl font-bold flex items-center gap-2">
          Processing Queue
          {activeJobs.length > 0 && (
            <span className="inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-blue-600 rounded-full">
              {activeJobs.length}
            </span>
          )}
        </h2>
        <button className="text-gray-500 hover:text-gray-700">
          <svg
            className={`w-5 h-5 transition-transform ${isCollapsed ? '' : 'rotate-180'}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
      </div>

      {/* Jobs List */}
      {!isCollapsed && (
        <div className="p-4">
          {activeJobs.length === 0 ? (
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
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="font-medium">No active jobs</p>
              <p className="text-sm">Submit a video to start processing</p>
            </div>
          ) : (
            <div className="space-y-4">
              {activeJobs.map((job) => (
                <div
                  key={job.id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                >
                  {/* Job Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 mb-1">
                        {job.video?.title || 'Processing video...'}
                      </h3>
                      {job.video?.url && (
                        <p className="text-sm text-gray-500 truncate">{job.video.url}</p>
                      )}
                    </div>
                    <JobStatusBadge status={job.status} />
                  </div>

                  {/* Progress Bar */}
                  <JobProgressBar progress={job.progress} status={job.status} />

                  {/* Job Footer */}
                  <div className="flex items-center justify-between mt-3 text-sm">
                    <span className="text-gray-600">
                      Elapsed: {getTimeElapsed(job.createdAt)}
                    </span>

                    <div className="flex gap-2">
                      {job.status === 'FAILED' && (
                        <button
                          onClick={(e) => handleRetry(job.id, e)}
                          disabled={retryJob.isPending}
                          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          Retry
                        </button>
                      )}
                      {(job.status === 'QUEUED' || job.status === 'PROCESSING') && (
                        <button
                          onClick={(e) => handleCancel(job.id, e)}
                          disabled={cancelJob.isPending}
                          className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Error Message */}
                  {job.status === 'FAILED' && job.error && (
                    <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                      {job.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
