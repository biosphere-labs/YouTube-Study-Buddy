import { cn } from '@/lib/utils';

interface SpinnerProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
};

export function Spinner({ className, size = 'md' }: SpinnerProps) {
  return (
    <div className="flex items-center justify-center">
      <div
        className={cn(
          'animate-spin rounded-full border-b-2 border-primary',
          sizeClasses[size],
          className
        )}
      />
    </div>
  );
}
