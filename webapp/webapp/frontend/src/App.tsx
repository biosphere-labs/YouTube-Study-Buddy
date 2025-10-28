import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect } from 'react';
import { Toaster } from 'sonner';
import { useAuth } from './hooks/useAuth';

// Pages
import { Login } from './pages/Login';
import { AuthCallback } from './pages/AuthCallback';
import { Dashboard } from './pages/Dashboard';
import { Videos } from './pages/Videos';
import { VideoDetailsPage } from './pages/VideoDetailsPage';
import { Notes } from './pages/Notes';
import { NoteDetails as NoteDetailsPage } from './pages/NoteDetailsPage';
import { Settings } from './pages/Settings';

// Components
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Spinner } from './components/ui/spinner';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppRoutes() {
  const { checkAuth, isLoading } = useAuth();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/auth/:provider/callback" element={<AuthCallback />} />

      {/* Protected Routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/videos"
        element={
          <ProtectedRoute>
            <Videos />
          </ProtectedRoute>
        }
      />
      <Route
        path="/videos/:id"
        element={
          <ProtectedRoute>
            <VideoDetailsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/notes"
        element={
          <ProtectedRoute>
            <Notes />
          </ProtectedRoute>
        }
      />
      <Route
        path="/notes/:id"
        element={
          <ProtectedRoute>
            <NoteDetailsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        }
      />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
        <Toaster position="top-right" richColors />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
