#!/bin/bash
set -e

echo "=== Creating YouTube Study Buddy Frontend Repository ==="

# Paths
OLD_REPO="/home/justin/Documents/dev/workspaces/ytstudybuddy"
NEW_REPO="/home/justin/Documents/dev/workspaces/YouTube-Study-Buddy-Frontend"

# Create new repository directory
echo "Creating new repository directory..."
mkdir -p "$NEW_REPO"
cd "$NEW_REPO"

# Initialize git
echo "Initializing git repository..."
git init
git branch -M main

# Copy frontend code
echo "Copying frontend application..."
cp -r "$OLD_REPO/frontend" "$NEW_REPO/"

# Copy related documentation
echo "Copying documentation..."
mkdir -p "$NEW_REPO/docs"
cp "$OLD_REPO/docs/OBSIDIAN-CLONE-INTEGRATION.md" "$NEW_REPO/docs/" 2>/dev/null || echo "  - OBSIDIAN-CLONE-INTEGRATION.md not found, skipping"

# Copy deployment configurations
echo "Copying deployment files..."
if [ -f "$OLD_REPO/.github/workflows/deploy.yml" ]; then
    mkdir -p "$NEW_REPO/.github/workflows"
    # Extract frontend-specific parts from deploy.yml
    echo "  - Note: You'll need to manually extract frontend deployment from deploy.yml"
fi

# Copy Docker configurations if they exist for frontend
echo "Checking for Docker configurations..."
if [ -d "$OLD_REPO/docker" ]; then
    # Only copy if there are frontend-related Docker files
    if ls "$OLD_REPO/docker"/*frontend* 1> /dev/null 2>&1; then
        mkdir -p "$NEW_REPO/docker"
        cp "$OLD_REPO/docker"/*frontend* "$NEW_REPO/docker/" 2>/dev/null || echo "  - No frontend Docker files found"
    fi
fi

# Create comprehensive README
echo "Creating README..."
cat > "$NEW_REPO/README.md" << 'EOF'
# YouTube Study Buddy - Frontend

Modern React TypeScript frontend for YouTube Study Buddy application.

## Overview

This is the web frontend for YouTube Study Buddy, a platform that transforms YouTube videos into structured study notes with AI-powered analysis.

## Tech Stack

- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 4
- **UI Components**: shadcn/ui + Lucide icons
- **Routing**: React Router 7
- **State Management**: Zustand + React Query
- **Authentication**: AWS Amplify + Cognito
- **HTTP Client**: Axios
- **Deployment**: AWS S3 + CloudFront (or your hosting platform)

## Project Structure

```
frontend/
├── public/                    # Static assets
├── src/
│   ├── api/                   # API clients for backend services
│   │   ├── auth.ts           # Authentication API
│   │   ├── client.ts         # Base API client configuration
│   │   ├── credits.ts        # Credits/billing API
│   │   ├── notes.ts          # Notes API
│   │   └── videos.ts         # Videos API
│   ├── components/
│   │   ├── Auth/             # Authentication components
│   │   ├── Credits/          # Credit management UI
│   │   ├── Dashboard/        # Main dashboard
│   │   ├── Layout/           # Layout components
│   │   ├── Notes/            # Notes viewer/editor
│   │   ├── ui/               # Reusable UI components (shadcn)
│   │   └── Videos/           # Video management UI
│   ├── hooks/                # Custom React hooks
│   │   ├── useAuth.ts        # Authentication hook
│   │   ├── useCredits.ts     # Credits management hook
│   │   └── usePolling.ts     # Polling utilities
│   ├── lib/                  # Utility libraries
│   │   ├── cognito.ts        # AWS Cognito utilities
│   │   └── utils.ts          # General utilities
│   ├── stores/               # Zustand state stores
│   │   ├── authStore.ts      # Auth state
│   │   └── uiStore.ts        # UI state
│   ├── types/                # TypeScript type definitions
│   ├── App.tsx               # Main application component
│   ├── aws-exports.ts        # AWS Amplify configuration
│   ├── index.css             # Global styles (Tailwind)
│   └── main.tsx              # Application entry point
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── DEV-MODE.md               # Development mode documentation
├── Dockerfile                # Docker container configuration
├── index.html                # HTML entry point
├── package.json              # NPM dependencies
├── postcss.config.js         # PostCSS configuration
├── TAILWIND-V4-MIGRATION.md  # Tailwind v4 migration guide
├── tsconfig.json             # TypeScript configuration
└── vite.config.ts            # Vite build configuration
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- AWS account (for Cognito authentication)
- Backend API running (see main YouTube Study Buddy repository)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd YouTube-Study-Buddy-Frontend
   ```

2. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Configure environment variables:
   ```bash
   cp frontend/.env.example frontend/.env
   ```

4. Edit `frontend/.env` with your configuration:
   ```bash
   # Backend API
   VITE_API_GATEWAY_URL=https://your-api-gateway-url

   # AWS Cognito
   VITE_COGNITO_USER_POOL_ID=us-east-1_xxx
   VITE_COGNITO_CLIENT_ID=xxx
   VITE_COGNITO_REGION=us-east-1

   # Stripe (if using payments)
   VITE_STRIPE_PUBLIC_KEY=pk_xxx

   # Development mode (bypass auth for local dev)
   VITE_DEV_MODE=true
   ```

### Development Mode

For rapid UI development without authentication:

```bash
cd frontend
npm run dev
```

With `VITE_DEV_MODE=true` in `.env`, you'll bypass the login page and go straight to the dashboard.

See `frontend/DEV-MODE.md` for full details.

### Production Build

```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`.

## Available Scripts

- `npm run dev` - Start development server (http://localhost:5173)
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint

## Features

### Authentication
- AWS Cognito integration
- Login/Signup with email
- Social login support (Google, Facebook)
- Session management

### Dashboard
- Overview statistics
- Recent video activity
- Quick access to notes

### Video Management
- Submit YouTube URLs for processing
- Real-time progress tracking
- Video history
- Batch processing support

### Notes
- View generated study notes
- Markdown rendering
- Wiki-style links
- Search and filter
- Export capabilities

### Credits System
- View credit balance
- Purchase credits
- Transaction history
- Stripe integration

## Backend Integration

This frontend connects to the YouTube Study Buddy backend API. The backend repository is:
- Repository: [YouTube Study Buddy Main](https://github.com/your-org/YouTube-Study-Buddy)
- API Documentation: See backend docs for API endpoints

### API Endpoints Used

- `GET /videos` - List videos
- `POST /videos` - Submit new video
- `GET /videos/{id}` - Get video details
- `GET /notes` - List notes
- `GET /notes/{id}` - Get note content
- `GET /credits/balance` - Get credit balance
- `POST /credits/purchase` - Purchase credits

## Deployment

### AWS S3 + CloudFront

1. Build the application:
   ```bash
   npm run build
   ```

2. Upload to S3:
   ```bash
   aws s3 sync frontend/dist/ s3://your-bucket-name/
   ```

3. Invalidate CloudFront cache:
   ```bash
   aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
   ```

### Docker

Build and run with Docker:

```bash
docker build -t ytstudybuddy-frontend -f frontend/Dockerfile .
docker run -p 5173:5173 ytstudybuddy-frontend
```

### Netlify/Vercel

1. Connect your repository
2. Set build command: `cd frontend && npm run build`
3. Set publish directory: `frontend/dist`
4. Add environment variables in platform settings

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_GATEWAY_URL` | Yes | Backend API endpoint URL |
| `VITE_COGNITO_USER_POOL_ID` | Yes | AWS Cognito User Pool ID |
| `VITE_COGNITO_CLIENT_ID` | Yes | AWS Cognito App Client ID |
| `VITE_COGNITO_REGION` | Yes | AWS region for Cognito |
| `VITE_STRIPE_PUBLIC_KEY` | No | Stripe publishable key (if using payments) |
| `VITE_DEV_MODE` | No | Set to `true` to bypass authentication locally |
| `VITE_ENABLE_ANALYTICS` | No | Enable analytics tracking |

### AWS Cognito Setup

1. Create a User Pool in AWS Cognito
2. Create an App Client (no secret)
3. Configure hosted UI (optional)
4. Add callback URLs for your frontend
5. Copy User Pool ID and App Client ID to `.env`

## Development

### Adding New Features

1. Create components in `src/components/`
2. Add API clients in `src/api/`
3. Create hooks in `src/hooks/` for reusable logic
4. Use Zustand stores in `src/stores/` for global state
5. Follow existing patterns for consistency

### Styling Guidelines

- Use Tailwind CSS utility classes
- Follow the design system defined in `index.css`
- Use shadcn/ui components from `src/components/ui/`
- Support dark mode where applicable

### Code Style

- TypeScript strict mode enabled
- ESLint for code quality
- Functional components with hooks
- Descriptive variable and function names

## Troubleshooting

### Dev server won't start
- Check Node.js version (18+)
- Delete `node_modules` and `package-lock.json`, reinstall
- Check for port conflicts (default: 5173)

### Authentication errors
- Verify Cognito configuration in `.env`
- Check Cognito callback URLs match your domain
- Ensure User Pool and App Client are correctly configured

### API errors
- Verify `VITE_API_GATEWAY_URL` is correct
- Check backend is running
- Verify CORS configuration on backend
- Check browser console for detailed errors

### Build failures
- Clear Vite cache: `rm -rf frontend/node_modules/.vite`
- Check for TypeScript errors: `npm run build`
- Verify all dependencies are installed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Your License]

## Related Repositories

- **Backend**: [YouTube Study Buddy](https://github.com/your-org/YouTube-Study-Buddy)
- **Documentation**: See main repository for architecture and API docs

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: See `/docs` directory
- Main Project: [YouTube Study Buddy Repository]
EOF

# Create .gitignore for frontend repo
echo "Creating .gitignore..."
cat > "$NEW_REPO/.gitignore" << 'EOF'
# Environment files
.env
.env.*.local
frontend/.env

# Dependencies
node_modules/
frontend/node_modules/

# Build outputs
dist/
dist-ssr/
frontend/dist/
frontend/dist-ssr/
*.local

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# Testing
coverage/
.nyc_output/

# Temporary files
*.tmp
*.temp
.cache/

# OS files
Thumbs.db
.DS_Store
EOF

# Create a docs directory with integration guide
echo "Creating documentation structure..."
mkdir -p "$NEW_REPO/docs"

# Create deployment guide
cat > "$NEW_REPO/docs/DEPLOYMENT.md" << 'EOF'
# Deployment Guide

## Overview

This guide covers deploying the YouTube Study Buddy frontend to various platforms.

## Prerequisites

- Built frontend (`npm run build` in `frontend/` directory)
- Environment variables configured
- Backend API running and accessible

## Deployment Options

### Option 1: AWS S3 + CloudFront (Recommended)

1. **Build the application**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Create S3 bucket**:
   ```bash
   aws s3 mb s3://ytstudybuddy-frontend
   ```

3. **Configure bucket for static website**:
   ```bash
   aws s3 website s3://ytstudybuddy-frontend --index-document index.html --error-document index.html
   ```

4. **Upload files**:
   ```bash
   aws s3 sync frontend/dist/ s3://ytstudybuddy-frontend/ --delete
   ```

5. **Create CloudFront distribution** (optional but recommended)

6. **Update environment variables** in your build process

### Option 2: Netlify

1. Connect repository to Netlify
2. Configure build settings:
   - Build command: `cd frontend && npm run build`
   - Publish directory: `frontend/dist`
3. Add environment variables in Netlify dashboard
4. Deploy

### Option 3: Vercel

1. Import project to Vercel
2. Configure:
   - Framework: Vite
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `dist`
3. Add environment variables
4. Deploy

### Option 4: Docker

Build and push to container registry:

```bash
docker build -t ytstudybuddy-frontend:latest -f frontend/Dockerfile .
docker push your-registry/ytstudybuddy-frontend:latest
```

Run container:

```bash
docker run -p 5173:5173 \
  -e VITE_API_GATEWAY_URL=https://api.example.com \
  -e VITE_COGNITO_USER_POOL_ID=us-east-1_xxx \
  -e VITE_COGNITO_CLIENT_ID=xxx \
  ytstudybuddy-frontend:latest
```

## Environment Variables

Ensure these are set in your deployment platform:

```bash
VITE_API_GATEWAY_URL=https://your-api.com
VITE_COGNITO_USER_POOL_ID=us-east-1_xxxxx
VITE_COGNITO_CLIENT_ID=xxxxx
VITE_COGNITO_REGION=us-east-1
VITE_STRIPE_PUBLIC_KEY=pk_xxxxx
VITE_ENABLE_ANALYTICS=true
```

**Never set `VITE_DEV_MODE=true` in production!**

## Post-Deployment

1. Test authentication flow
2. Verify API connectivity
3. Test all main features
4. Check browser console for errors
5. Test on multiple devices/browsers

## Troubleshooting

### White screen on deployment
- Check browser console
- Verify base URL in `vite.config.ts`
- Ensure all environment variables are set

### API errors
- Verify CORS settings on backend
- Check API URL is correct
- Verify SSL certificates

### Authentication failures
- Check Cognito callback URLs include your domain
- Verify Cognito configuration
- Check browser cookies are enabled
EOF

# Add the initial commit
echo "Creating initial commit..."
cd "$NEW_REPO"
git add .
git commit -m "Initial commit: YouTube Study Buddy Frontend

- React 19 + TypeScript + Vite 7
- Tailwind CSS 4 + shadcn/ui
- AWS Amplify + Cognito authentication
- Complete dashboard, videos, notes, credits pages
- Development mode for local testing
- Comprehensive documentation

Separated from main YouTube Study Buddy repository for
independent development and deployment."

echo ""
echo "=== Frontend Repository Created Successfully! ==="
echo ""
echo "Location: $NEW_REPO"
echo ""
echo "Next steps:"
echo "1. cd $NEW_REPO"
echo "2. Create remote repository on GitHub"
echo "3. git remote add origin <remote-url>"
echo "4. git push -u origin main"
echo ""
echo "To run locally:"
echo "  cd $NEW_REPO/frontend"
echo "  npm install"
echo "  npm run dev"
echo ""
