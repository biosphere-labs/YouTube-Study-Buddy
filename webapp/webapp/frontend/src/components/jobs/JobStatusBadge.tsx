import React from 'react';

interface JobStatusBadgeProps {
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  className?: string;
}

export const JobStatusBadge: React.FC<JobStatusBadgeProps> = ({ status, className = '' }) => {
  const getStatusStyles = () => {
    switch (status) {
      case 'QUEUED':
        return 'bg-gray-100 text-gray-800 border-gray-300';
      case 'PROCESSING':
        return 'bg-blue-100 text-blue-800 border-blue-300 animate-pulse';
      case 'COMPLETED':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'FAILED':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'QUEUED':
        return 'ó';
      case 'PROCESSING':
        return '™';
      case 'COMPLETED':
        return '';
      case 'FAILED':
        return 'L';
      default:
        return 'S';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'QUEUED':
        return 'Queued';
      case 'PROCESSING':
        return 'Processing';
      case 'COMPLETED':
        return 'Completed';
      case 'FAILED':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${getStatusStyles()} ${className}`}
      title={`Status: ${getStatusText()}`}
    >
      <span>{getStatusIcon()}</span>
      <span>{getStatusText()}</span>
    </span>
  );
};
