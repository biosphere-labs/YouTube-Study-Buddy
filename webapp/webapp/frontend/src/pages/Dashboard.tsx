import { Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { AppLayout } from '@/components/layout/AppLayout';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Video, FileText, Clock, ArrowRight } from 'lucide-react';

export function Dashboard() {
  const { user } = useAuth();

  // Placeholder stats - will be replaced with actual data
  const stats = {
    totalVideos: 0,
    totalNotes: 0,
    activeJobs: 0,
  };

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Welcome Section */}
        <div>
          <h1 className="text-4xl font-bold tracking-tight">
            Welcome back{user?.name ? `, ${user.name}` : ''}!
          </h1>
          <p className="text-muted-foreground mt-2">
            Transform your YouTube videos into comprehensive study notes with AI
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Videos</CardTitle>
              <Video className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalVideos}</div>
              <p className="text-xs text-muted-foreground">
                Videos processed
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Study Notes</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalNotes}</div>
              <p className="text-xs text-muted-foreground">
                Notes generated
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.activeJobs}</div>
              <p className="text-xs text-muted-foreground">
                Currently processing
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Video className="h-5 w-5" />
                Submit New Video
              </CardTitle>
              <CardDescription>
                Add a YouTube URL to generate study notes and assessments
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link to="/videos">
                <Button className="w-full">
                  Go to Videos
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                View Your Notes
              </CardTitle>
              <CardDescription>
                Browse and search through all your generated study materials
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link to="/notes">
                <Button variant="outline" className="w-full">
                  Go to Notes
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Getting Started */}
        {stats.totalVideos === 0 && (
          <Card className="border-dashed">
            <CardHeader>
              <CardTitle>Get Started</CardTitle>
              <CardDescription>
                You haven't processed any videos yet. Here's how to begin:
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ol className="space-y-3 text-sm">
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                    1
                  </span>
                  <span>Go to the Videos page and paste a YouTube URL</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                    2
                  </span>
                  <span>Choose your subject and options (assessments, etc.)</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                    3
                  </span>
                  <span>Wait for AI to generate comprehensive study notes</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                    4
                  </span>
                  <span>Access your notes and start studying!</span>
                </li>
              </ol>
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}
