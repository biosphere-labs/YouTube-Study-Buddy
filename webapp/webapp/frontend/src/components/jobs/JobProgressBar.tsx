import React from 'react';

interface JobProgressBarProps {
  progress: number;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  statusText?: string;
  className?: string;
}

export const JobProgressBar: React.FC<JobProgressBarProps> = ({
  progress,
  status,
  statusText,
  className = '',
}) => {
  const getProgressBarColor = () => {
    switch (status) {
      case 'QUEUED':
        return 'bg-gray-400';
      case 'PROCESSING':
        return 'bg-blue-500';
      case 'COMPLETED':
        return 'bg-green-500';
      case 'FAILED':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getBackgroundColor = () => {
    switch (status) {
      case 'FAILED':
        return 'bg-red-100';
      case 'COMPLETED':
        return 'bg-green-100';
      default:
        return 'bg-gray-200';
    }
  };

  const getStatusMessage = () => {
    if (statusText) return statusText;

    switch (status) {
      case 'QUEUED':
        return 'Waiting in queue...';
      case 'PROCESSING':
        if (progress < 20) return 'Extracting transcript...';
        if (progress < 50) return 'Analyzing content...';
        if (progress < 80) return 'Generating notes...';
        return 'Finalizing...';
      case 'COMPLETED':
        return 'Processing complete!';
      case 'FAILED':
        return 'Processing failed';
      default:
        return '';
    }
  };

  // For queued jobs, show indeterminate progress
  const isIndeterminate = status === 'QUEUED';
  const displayProgress = Math.min(Math.max(progress, 0), 100);

  return (
    <div className={`w-full ${className}`}>
      {/* Progress bar */}
      <div className={`relative h-3 ${getBackgroundColor()} rounded-full overflow-hidden`}>
        {isIndeterminate ? (
          // Indeterminate animation for queued jobs
          <div className={`h-full ${getProgressBarColor()} animate-pulse w-full`} />
        ) : (
          // Determinate progress bar
          <div
            className={`h-full ${getProgressBarColor()} transition-all duration-300 ease-out`}
            style={{ width: `${displayProgress}%` }}
          />
        )}
      </div>

      {/* Status text and percentage */}
      <div className="flex justify-between items-center mt-2 text-sm">
        <span className="text-gray-600">{getStatusMessage()}</span>
        {!isIndeterminate && (
          <span className="text-gray-700 font-medium">{displayProgress}%</span>
        )}
      </div>
    </div>
  );
};
