# YouTube Study Buddy - React Frontend

A modern React TypeScript frontend for YouTube Study Buddy that allows users to transform YouTube videos into comprehensive study notes.

## Features

- **Authentication**: Social login with Google, GitHub, and Discord
- **Video Processing**: Submit YouTube URLs for automated transcript extraction and note generation
- **Real-time Updates**: WebSocket integration for live progress tracking
- **Note Management**: View, edit, and export study notes in Markdown format
- **Credit System**: Purchase and track credit usage for video processing
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Dark Mode**: Built-in theme switching

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **React Router** for client-side routing
- **TanStack Query** for data fetching and caching
- **Zustand** for state management
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components
- **Axios** for HTTP requests
- **Socket.io** for WebSocket connections
- **React Markdown** for rendering notes

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Update .env with your API URL
# VITE_API_BASE_URL=http://localhost:8000
# VITE_WS_URL=ws://localhost:8000
```

### Development

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## API Integration

The frontend expects the following API endpoints:

- `POST /auth/{provider}` - Initialize OAuth flow
- `POST /auth/{provider}/callback` - Handle OAuth callback
- `GET /auth/me` - Get current user
- `POST /auth/logout` - Logout
- `POST /videos` - Submit video
- `GET /videos` - List videos
- `GET /videos/:id` - Get video details
- `POST /videos/:id/retry` - Retry failed video
- `DELETE /videos/:id` - Delete video
- `GET /notes` - List notes
- `GET /notes/:id` - Get note details
- `PATCH /notes/:id` - Update note
- `DELETE /notes/:id` - Delete note
- `GET /notes/:id/export` - Export note
- `GET /credits/balance` - Get credit balance
- `GET /credits/transactions` - Get transaction history
- `POST /credits/purchase` - Purchase credits
- `GET /credits/usage` - Get usage stats
