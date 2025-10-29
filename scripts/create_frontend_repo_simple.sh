#!/bin/bash
# Simple script to create frontend repository

OLD="/home/justin/Documents/dev/workspaces/ytstudybuddy"
NEW="/home/justin/Documents/dev/workspaces/YouTube-Study-Buddy-Frontend"

echo "Creating directory..."
mkdir -p "$NEW"

echo "Copying frontend..."
cp -r "$OLD/frontend" "$NEW/"

echo "Creating docs directory..."
mkdir -p "$NEW/docs"

echo "Copying Obsidian doc if exists..."
cp "$OLD/docs/OBSIDIAN-CLONE-INTEGRATION.md" "$NEW/docs/" 2>/dev/null || echo "Obsidian doc not found"

echo "Creating README..."
cd "$NEW"

cat > README.md << 'ENDREADME'
# YouTube Study Buddy - Frontend

React TypeScript frontend for YouTube Study Buddy.

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

## Tech Stack

- React 19 + TypeScript
- Vite 7
- Tailwind CSS 4
- AWS Amplify + Cognito
- React Router 7

## Environment Setup

Copy `frontend/.env.example` to `frontend/.env` and configure:

```bash
VITE_API_GATEWAY_URL=your-api-url
VITE_COGNITO_USER_POOL_ID=your-pool-id
VITE_COGNITO_CLIENT_ID=your-client-id
VITE_DEV_MODE=true  # For local development
```

## Development Mode

Set `VITE_DEV_MODE=true` in `.env` to bypass authentication during development.

See `frontend/DEV-MODE.md` for details.

## Build

```bash
cd frontend
npm run build
```

## Backend

Backend repository: [YouTube-Study-Buddy](https://github.com/your-username/YouTube-Study-Buddy)

## Documentation

- `frontend/DEV-MODE.md` - Development mode guide
- `frontend/TAILWIND-V4-MIGRATION.md` - Tailwind v4 migration
- `docs/OBSIDIAN-CLONE-INTEGRATION.md` - Obsidian integration

ENDREADME

cat > .gitignore << 'ENDIGNORE'
# Environment
.env
.env.*.local
frontend/.env

# Dependencies
node_modules/
frontend/node_modules/

# Build
dist/
dist-ssr/
frontend/dist/
frontend/dist-ssr/
*.local

# Logs
*.log

# Editor
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store

# Testing
coverage/

ENDIGNORE

echo "Initializing git..."
git init
git branch -M main
git add .
git commit -m "Initial commit: YouTube Study Buddy Frontend

- React 19 + TypeScript + Vite 7
- Tailwind CSS 4 + shadcn/ui
- AWS Amplify + Cognito authentication
- Complete dashboard, videos, notes, credits pages
- Development mode for local testing

Separated from main repository for independent development."

echo ""
echo "✅ Frontend repository created at:"
echo "   $NEW"
echo ""
echo "Next steps:"
echo "1. cd $NEW"
echo "2. Test: cd frontend && npm install && npm run dev"
echo "3. Create GitHub repo: https://github.com/new"
echo "4. git remote add origin <your-repo-url>"
echo "5. git push -u origin main"
