# Agent Task: Frontend Authentication & User Management

## Branch: `feature/frontend-auth`

## Objective
Set up React frontend with authentication, routing, and user session management using OverInnovate components.

## Tasks

### 1. React + Vite Project Setup
- Initialize Vite project in `webapp/frontend/`
- Configure TypeScript strict mode
- Set up Tailwind CSS
- Configure path aliases (@/ = src/)
- Set up ESLint and Prettier

### 2. Install Core Dependencies
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend

# Core dependencies
npm install react react-dom react-router-dom
npm install @tanstack/react-router @tanstack/react-query
npm install zustand
npm install axios

# UI dependencies
npm install tailwindcss postcss autoprefixer
npm install @radix-ui/react-icons
npm install clsx tailwind-merge

# shadcn/ui setup
npx shadcn-ui@latest init

# OverInnovate (if available via npm, otherwise manual integration)
# npm install @overinnovate/ui
```

### 3. Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn components
│   │   ├── auth/            # Auth-specific components
│   │   ├── layout/          # Layout components
│   │   └── shared/          # Shared components
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   └── Settings.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useUser.ts
│   │   └── useApi.ts
│   ├── lib/
│   │   ├── api.ts           # Axios instance
│   │   ├── auth.ts          # Auth utilities
│   │   └── utils.ts         # General utilities
│   ├── stores/
│   │   └── authStore.ts     # Zustand auth store
│   ├── types/
│   │   ├── auth.ts
│   │   └── user.ts
│   ├── App.tsx
│   └── main.tsx
```

### 4. Routing Setup (TanStack Router)
- Configure router with routes:
  - `/login` - Login page (public)
  - `/auth/callback` - OAuth callback handler (public)
  - `/dashboard` - Dashboard (protected)
  - `/videos` - Videos list (protected)
  - `/videos/:id` - Video details (protected)
  - `/notes` - Notes list (protected)
  - `/notes/:id` - Note viewer (protected)
  - `/settings` - User settings (protected)
- Implement route guards for protected routes
- Implement redirect logic (login → dashboard, protected → login)

### 5. Authentication Context & Store
```typescript
// stores/authStore.ts
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}
```

### 6. API Client Setup
```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add auth token
api.interceptors.request.use((config) => {
  const token = authStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      authStore.getState().logout();
    }
    return Promise.reject(error);
  }
);
```

### 7. Login Page with OverInnovate
- Create `pages/Login.tsx`
- Integrate OverInnovate social sign-in buttons:
  - Google sign-in
  - GitHub sign-in
  - Discord sign-in
- Handle OAuth redirect flow
- Display loading states
- Handle errors

### 8. OAuth Callback Handler
- Create `pages/AuthCallback.tsx`
- Parse query parameters (code, state, error)
- Exchange code for JWT token
- Store token and user data
- Redirect to dashboard
- Handle OAuth errors

### 9. Protected Route Component
```typescript
// components/auth/ProtectedRoute.tsx
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <LoadingSpinner />;
  if (!isAuthenticated) return <Navigate to="/login" />;

  return <>{children}</>;
}
```

### 10. Layout Components
- Create `components/layout/AppLayout.tsx`:
  - Top navigation bar
  - User avatar and menu
  - Logout button
  - Responsive sidebar (mobile menu)
- Create `components/layout/AuthLayout.tsx`:
  - Centered container for login page
  - Branding/logo

### 11. User Profile & Settings
- Create `pages/Settings.tsx`
- Display user profile information
- API key management (for Claude API)
- Account settings
- Logout button

### 12. Dashboard Page (Skeleton)
- Create `pages/Dashboard.tsx`
- Display user name and avatar
- Show quick stats (placeholders):
  - Total videos processed
  - Total notes created
  - Active jobs
- Navigation links to videos and notes

### 13. Auth Hooks
```typescript
// hooks/useAuth.ts
export function useAuth() {
  const { user, token, isAuthenticated, login, logout } = useAuthStore();
  // ... additional logic
}

// hooks/useUser.ts
export function useUser() {
  return useQuery({
    queryKey: ['user'],
    queryFn: () => api.get('/auth/me').then(res => res.data),
    enabled: !!authStore.getState().token,
  });
}
```

### 14. TypeScript Types
```typescript
// types/auth.ts
export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  githubId?: string;
  googleId?: string;
  discordId?: string;
  createdAt: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

// types/api.ts
export interface ApiError {
  statusCode: number;
  message: string;
  error: string;
}
```

## Dependencies to Install
```bash
npm install react react-dom
npm install @tanstack/react-router @tanstack/react-query
npm install zustand
npm install axios
npm install tailwindcss postcss autoprefixer
npm install clsx tailwind-merge
```

## Success Criteria
- ✅ Vite dev server runs successfully
- ✅ Routing works correctly (public and protected routes)
- ✅ Login page displays OverInnovate social sign-in buttons
- ✅ OAuth flow completes and user is authenticated
- ✅ JWT token is stored and sent with API requests
- ✅ Protected routes redirect to login when not authenticated
- ✅ User avatar and name displayed in nav bar
- ✅ Logout clears token and redirects to login
- ✅ 401 responses trigger logout
- ✅ Dashboard displays user information

## Pages to Implement
```
/login             - Social sign-in page
/auth/callback     - OAuth callback handler
/dashboard         - User dashboard (skeleton)
/settings          - User settings and API key
```

## Environment Variables
```env
VITE_API_URL=http://localhost:3000
VITE_WS_URL=ws://localhost:3000
```

## Testing
- Test login flow with each OAuth provider
- Test protected route redirects
- Test logout functionality
- Test token refresh logic
- Test API error handling (401, 403, 500)

## Integration Points
- Exports `<ProtectedRoute>` component
- Exports `useAuth()` and `useUser()` hooks
- Exports `api` client for use by other modules
- Provides auth context for entire app
- Ready for Videos and Notes modules to consume

## Notes
- Store JWT token in localStorage (or httpOnly cookie if backend supports)
- Implement token expiration handling
- Add loading states for all async operations
- Use React Query for server state management
- Use Zustand for client state (auth, UI state)
- Follow shadcn/ui patterns for component composition
- Implement proper TypeScript types throughout
- Add error boundaries for graceful error handling
- Consider implementing refresh token logic if backend supports it
