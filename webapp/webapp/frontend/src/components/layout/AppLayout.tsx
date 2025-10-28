import { Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { LogOut, Settings, User, Video, FileText, LayoutDashboard } from 'lucide-react';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4">
          {/* Logo and Brand */}
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Video className="h-5 w-5" />
              </div>
              <span className="text-xl font-bold">YouTube Study Buddy</span>
            </Link>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center gap-1">
              <Link to="/dashboard">
                <Button variant="ghost" size="sm">
                  <LayoutDashboard className="h-4 w-4 mr-2" />
                  Dashboard
                </Button>
              </Link>
              <Link to="/videos">
                <Button variant="ghost" size="sm">
                  <Video className="h-4 w-4 mr-2" />
                  Videos
                </Button>
              </Link>
              <Link to="/notes">
                <Button variant="ghost" size="sm">
                  <FileText className="h-4 w-4 mr-2" />
                  Notes
                </Button>
              </Link>
            </nav>
          </div>

          {/* User Menu */}
          <div className="flex items-center gap-4">
            {user && (
              <div className="flex items-center gap-3">
                {/* User Info */}
                <div className="hidden md:block text-right">
                  <div className="text-sm font-medium">{user.name || user.email}</div>
                  <div className="text-xs text-muted-foreground">{user.email}</div>
                </div>

                {/* User Avatar */}
                {user.avatar ? (
                  <img
                    src={user.avatar}
                    alt={user.name || 'User'}
                    className="h-9 w-9 rounded-full border-2 border-border"
                  />
                ) : (
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground">
                    <User className="h-5 w-5" />
                  </div>
                )}

                {/* Settings Button */}
                <Link to="/settings">
                  <Button variant="ghost" size="icon">
                    <Settings className="h-5 w-5" />
                  </Button>
                </Link>

                {/* Logout Button */}
                <Button variant="ghost" size="icon" onClick={handleLogout}>
                  <LogOut className="h-5 w-5" />
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">{children}</main>
    </div>
  );
}
