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
import { User, Key, LogOut } from 'lucide-react';

export function Settings() {
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
    <AppLayout>
      <div className="space-y-8 max-w-4xl">
        {/* Page Header */}
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-2">
            Manage your account and application preferences
          </p>
        </div>

        {/* User Profile */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Profile Information
            </CardTitle>
            <CardDescription>
              Your account details from OAuth provider
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              {user?.avatar ? (
                <img
                  src={user.avatar}
                  alt={user.name || 'User'}
                  className="h-16 w-16 rounded-full border-2 border-border"
                />
              ) : (
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground">
                  <User className="h-8 w-8" />
                </div>
              )}
              <div>
                <div className="text-lg font-semibold">
                  {user?.name || 'User'}
                </div>
                <div className="text-sm text-muted-foreground">{user?.email}</div>
              </div>
            </div>

            <div className="grid gap-3 pt-4 border-t">
              <div className="grid grid-cols-3 gap-4">
                <div className="text-sm font-medium text-muted-foreground">
                  User ID:
                </div>
                <div className="text-sm col-span-2 font-mono">{user?.id}</div>
              </div>

              {user?.githubId && (
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-sm font-medium text-muted-foreground">
                    GitHub:
                  </div>
                  <div className="text-sm col-span-2">Connected</div>
                </div>
              )}

              {user?.googleId && (
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-sm font-medium text-muted-foreground">
                    Google:
                  </div>
                  <div className="text-sm col-span-2">Connected</div>
                </div>
              )}

              {user?.discordId && (
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-sm font-medium text-muted-foreground">
                    Discord:
                  </div>
                  <div className="text-sm col-span-2">Connected</div>
                </div>
              )}

              <div className="grid grid-cols-3 gap-4">
                <div className="text-sm font-medium text-muted-foreground">
                  Member Since:
                </div>
                <div className="text-sm col-span-2">
                  {user?.createdAt
                    ? new Date(user.createdAt).toLocaleDateString()
                    : 'N/A'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Key Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              Claude API Key
            </CardTitle>
            <CardDescription>
              Configure your Claude API key for generating study notes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground mb-4">
                  You can either use the system-wide API key or provide your own
                  Claude API key for personalized usage tracking and billing.
                </p>
                <Button variant="outline" disabled>
                  Manage API Key (Coming Soon)
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Account Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Account Actions</CardTitle>
            <CardDescription>Manage your account and sessions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Button
                variant="destructive"
                onClick={handleLogout}
                className="w-full sm:w-auto"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Sign Out
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
