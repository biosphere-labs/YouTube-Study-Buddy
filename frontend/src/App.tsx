import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LoginPage } from './components/Auth/LoginPage';
import { MainLayout } from './components/Layout/MainLayout';
import { Dashboard } from './components/Dashboard/Dashboard';
import { VideoList } from './components/Videos/VideoList';
import { NoteList } from './components/Notes/NoteList';
import { NoteViewer } from './components/Notes/NoteViewer';
import { CreditBalance } from './components/Credits/CreditBalance';
import { TransactionHistory } from './components/Credits/TransactionHistory';
import { useAuth } from './hooks/useAuth';
import { useAuthStore } from './stores/authStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function CreditsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Credits</h1>
        <p className="text-muted-foreground">
          Manage your credit balance and view transaction history
        </p>
      </div>
      <div className="grid gap-6 md:grid-cols-2">
        <CreditBalance />
        <TransactionHistory />
      </div>
    </div>
  );
}

function App() {
  const initAuth = useAuthStore((state) => state.initAuth);

  // Initialize auth state on app mount
  useEffect(() => {
    initAuth();
  }, [initAuth]);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/callback" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="videos" element={<VideoList />} />
            <Route path="notes" element={<NoteList />} />
            <Route path="notes/:id" element={<NoteViewer />} />
            <Route path="credits" element={<CreditsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
