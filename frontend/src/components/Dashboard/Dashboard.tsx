import { useQuery } from '@tanstack/react-query';
import { Video, FileText, CreditCard, TrendingUp } from 'lucide-react';
import { StatsCard } from './StatsCard';
import { RecentVideos } from './RecentVideos';
import { useCredits } from '@/hooks/useCredits';
import { videosApi } from '@/api/videos';

export function Dashboard() {
  const { balance, usageStats, isLoading: isLoadingCredits } = useCredits();

  const { data: videosData, isLoading: isLoadingVideos } = useQuery({
    queryKey: ['videos'],
    queryFn: () => videosApi.getVideos(),
  });

  const recentVideos = videosData?.videos?.slice(0, 5) || [];

  if (isLoadingCredits || isLoadingVideos) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back! Here's an overview of your activity.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Credit Balance"
          value={balance?.balance || 0}
          description="Available credits"
          icon={CreditCard}
        />
        <StatsCard
          title="Videos This Month"
          value={usageStats?.videosProcessedThisMonth || 0}
          description="Videos processed"
          icon={Video}
        />
        <StatsCard
          title="Total Videos"
          value={usageStats?.totalVideosProcessed || 0}
          description="All time"
          icon={FileText}
        />
        <StatsCard
          title="Credits Used"
          value={usageStats?.creditsUsedThisMonth || 0}
          description="This month"
          icon={TrendingUp}
        />
      </div>

      <RecentVideos videos={recentVideos} />
    </div>
  );
}
