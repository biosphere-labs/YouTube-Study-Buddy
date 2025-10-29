# Development Mode

## Overview

The frontend supports a **Development Mode** that bypasses authentication for local development and testing. This allows you to access all pages without needing to configure AWS Cognito or log in.

## Enabling Development Mode

### Option 1: Environment Variable (Recommended)

Edit `.env` file:

```bash
# Development Mode (bypasses authentication)
VITE_DEV_MODE=true
```

Then restart the dev server:

```bash
npm run dev
```

### Option 2: Inline in Code

Set it directly when running:

```bash
VITE_DEV_MODE=true npm run dev
```

## What Happens in Dev Mode

When `VITE_DEV_MODE=true`:

1. ✅ **Authentication is bypassed** - You go straight to the dashboard
2. ✅ **Protected routes are accessible** - No redirect to login page
3. ✅ **Login page redirects to dashboard** - Visiting `/login` redirects to `/`
4. ✅ **Auth initialization is skipped** - No AWS Cognito calls
5. ✅ **All pages are accessible** - Dashboard, Videos, Notes, Credits

## Pages You Can Access

With dev mode enabled, you can navigate directly to:

- `/` - Dashboard
- `/videos` - Video List
- `/notes` - Note List
- `/notes/:id` - Individual Note Viewer
- `/credits` - Credits & Transaction History

## Disabling Dev Mode

To require authentication again, edit `.env`:

```bash
# Development Mode (bypasses authentication)
VITE_DEV_MODE=false
```

Or remove the variable entirely (defaults to `false`).

## Production Safety

⚠️ **Important**: The `.env` file should **never** be committed with `VITE_DEV_MODE=true`.

- ✅ `.env.example` has `VITE_DEV_MODE=false` (safe default)
- ✅ `.env` is gitignored (your local settings won't be committed)
- ✅ Production builds should never have this enabled

## How It Works

### Code Changes

**`src/App.tsx`**:

```typescript
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const devMode = import.meta.env.VITE_DEV_MODE === 'true';

  // Bypass authentication in development mode
  if (devMode) {
    return <>{children}</>;
  }

  // Normal auth flow...
}
```

**Auth Initialization**:

```typescript
function App() {
  const initAuth = useAuthStore((state) => state.initAuth);
  const devMode = import.meta.env.VITE_DEV_MODE === 'true';

  useEffect(() => {
    if (!devMode) {
      initAuth(); // Skip Cognito setup in dev mode
    }
  }, [initAuth, devMode]);
}
```

## Use Cases

### Local UI Development

```bash
VITE_DEV_MODE=true npm run dev
```

Perfect for:
- Designing components
- Testing layouts
- Debugging UI issues
- Working on features without AWS credentials

### Testing Authentication

```bash
VITE_DEV_MODE=false npm run dev
```

Required for:
- Testing login flow
- Verifying Cognito integration
- Testing authenticated API calls
- Pre-production testing

## Environment Variables Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_DEV_MODE` | boolean | `false` | Bypass authentication for local dev |
| `VITE_API_GATEWAY_URL` | string | - | Backend API endpoint |
| `VITE_COGNITO_USER_POOL_ID` | string | - | AWS Cognito User Pool |
| `VITE_COGNITO_CLIENT_ID` | string | - | AWS Cognito Client ID |
| `VITE_COGNITO_REGION` | string | - | AWS Region |
| `VITE_STRIPE_PUBLIC_KEY` | string | - | Stripe Publishable Key |
| `VITE_ENABLE_ANALYTICS` | boolean | `false` | Enable analytics tracking |

## Troubleshooting

### Dev mode not working?

1. Check `.env` file has `VITE_DEV_MODE=true`
2. Restart the dev server (Vite needs restart for env changes)
3. Clear browser cache and reload
4. Check browser console for errors

### Still seeing login page?

```bash
# Force restart with dev mode
npm run dev -- --force
```

### API calls failing?

Dev mode bypasses **auth**, but API calls still need valid endpoints:
- Set `VITE_API_GATEWAY_URL` in `.env`
- Or mock API responses for offline development

## Security Notes

- 🔒 Dev mode only works with Vite dev server
- 🔒 Production builds ignore this setting
- 🔒 Never deploy with `VITE_DEV_MODE=true`
- 🔒 Always use real auth for staging/production

## Related Files

- `.env` - Your local environment config (gitignored)
- `.env.example` - Template with safe defaults
- `src/App.tsx` - App routing and auth logic
- `src/hooks/useAuth.ts` - Authentication hook
- `src/stores/authStore.ts` - Auth state management
