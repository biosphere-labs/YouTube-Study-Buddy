import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { authApi } from '@/lib/auth';
import { Spinner } from '@/components/ui/spinner';
import { Card, CardContent } from '@/components/ui/card';

export function AuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Extract code and provider from URL
        const code = searchParams.get('code');
        const provider = window.location.pathname.split('/').pop() || '';
        const errorParam = searchParams.get('error');

        if (errorParam) {
          setError('Authentication failed. Please try again.');
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        if (!code) {
          setError('No authorization code received.');
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        // Exchange code for token
        const response = await authApi.handleOAuthCallback(provider, code);

        // Login with the received token
        await login(response.token);

        // Redirect to dashboard
        navigate('/dashboard');
      } catch (err) {
        console.error('OAuth callback error:', err);
        setError('Authentication failed. Please try again.');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleCallback();
  }, [login, navigate, searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          {error ? (
            <div className="text-center">
              <div className="text-destructive text-lg font-semibold mb-2">
                {error}
              </div>
              <p className="text-muted-foreground text-sm">
                Redirecting to login...
              </p>
            </div>
          ) : (
            <div className="text-center space-y-4">
              <Spinner size="lg" />
              <div>
                <h2 className="text-xl font-semibold">Authenticating...</h2>
                <p className="text-muted-foreground text-sm mt-2">
                  Please wait while we complete your sign-in
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
