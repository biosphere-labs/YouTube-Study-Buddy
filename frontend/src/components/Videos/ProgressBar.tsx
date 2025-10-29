import { Progress } from '@/components/ui/progress';

interface ProgressBarProps {
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}

export function ProgressBar({ progress, status }: ProgressBarProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'processing':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'processing':
        return `Processing (${progress}%)`;
      default:
        return 'Pending';
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">{getStatusText()}</span>
        <span className="font-medium">{progress}%</span>
      </div>
      <Progress value={progress} className={getStatusColor()} />
    </div>
  );
}
