import { Link, Outlet, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import { useUIStore } from '@/stores/uiStore';
import {
  LayoutDashboard,
  Video,
  FileText,
  CreditCard,
  Menu,
  LogOut,
  Moon,
  Sun,
} from 'lucide-react';

export function MainLayout() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme, sidebarOpen, toggleSidebar } = useUIStore();
  const location = useLocation();

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/videos', label: 'Videos', icon: Video },
    { to: '/notes', label: 'Notes', icon: FileText },
    { to: '/credits', label: 'Credits', icon: CreditCard },
  ];

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              className="md:hidden"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <h1 className="text-xl font-bold">YouTube Study Buddy</h1>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={toggleTheme}>
              {theme === 'light' ? (
                <Moon className="h-5 w-5" />
              ) : (
                <Sun className="h-5 w-5" />
              )}
            </Button>

            {user && (
              <div className="flex items-center gap-3">
                <div className="hidden md:block text-right">
                  <p className="text-sm font-medium">{user.name || user.email}</p>
                  <p className="text-xs text-muted-foreground">{user.provider}</p>
                </div>
                {user.avatar && (
                  <img
                    src={user.avatar}
                    alt={user.name || 'User'}
                    className="h-8 w-8 rounded-full"
                  />
                )}
                <Button variant="ghost" size="icon" onClick={logout}>
                  <LogOut className="h-5 w-5" />
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="container flex px-4 py-6">
        {/* Sidebar */}
        <aside
          className={`${
            sidebarOpen ? 'block' : 'hidden'
          } md:block w-64 mr-6 space-y-2`}
        >
          <nav className="space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent transition-colors ${
                  isActive(item.to) ? 'bg-accent text-accent-foreground' : ''
                }`}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
