# Quick Frontend Review Guide

## TL;DR - How to See the React Frontend Right Now

```bash
cd react-frontend/frontend
npm install
npm run dev
```

Then open http://localhost:5173 in your browser.

### Skip Login for Development

The `.env` file is already configured with `VITE_DEV_MODE=true`, which bypasses authentication. You'll go straight to the dashboard without needing to log in.

To require login again, edit `.env` and set:
```bash
VITE_DEV_MODE=false
```

See `frontend/DEV-MODE.md` for full documentation.

---

## What You'll See

A modern React application with:
- **Authentication**: AWS Cognito integration with login/signup
- **Dashboard**: Main overview page
- **Videos**: YouTube video management
- **Notes**: Study notes interface
- **Modern Stack**: React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui

---

## Frontend Code Location

The React frontend code lives in:
```
react-frontend/frontend/
├── src/
│   ├── api/          # API client for backend
│   ├── components/   # React components
│   ├── hooks/        # Custom React hooks
│   ├── lib/          # Utilities
│   ├── routes/       # Routing
│   ├── stores/       # Zustand state management
│   ├── types/        # TypeScript types
│   ├── App.tsx       # Main app component
│   └── main.tsx      # Entry point
├── package.json
└── vite.config.ts
```

---

## Tech Stack

```json
{
  "framework": "React 19 + TypeScript",
  "build": "Vite 7",
  "styling": "Tailwind CSS 4",
  "routing": "React Router 7",
  "state": "Zustand + React Query",
  "auth": "AWS Amplify + Cognito",
  "http": "Axios",
  "ui": "shadcn/ui + Lucide icons"
}
```

---

## Mystery Solved: The `frontend/` Directory

**Location**: `/home/justin/Documents/dev/workspaces/ytstudybuddy/frontend/`

**Contents**: Only a Dockerfile (771 bytes)

**Status**:
- ❌ Not tracked in any git branch
- ❌ Not referenced by CI/CD
- ❌ Not a worktree
- ⚠️ Likely orphaned from earlier development

**Recommendation**:
- Either delete it (it's not used)
- Or move the Dockerfile to `react-frontend/frontend/Dockerfile` where the actual React code is

**Note**: The actual React frontend doesn't currently have a Dockerfile. The orphaned one in `frontend/` could be moved to the correct location if you plan to containerize the frontend.

---

## File Structure Summary

```
ytstudybuddy/
│
├── react-frontend/               # Worktree directory (ignored)
│   └── frontend/                 # ⭐ ACTUAL REACT CODE HERE ⭐
│       ├── src/
│       ├── package.json
│       └── vite.config.ts
│
├── frontend/                     # ❓ Orphaned directory
│   └── Dockerfile                # Could be moved to react-frontend/frontend/
│
├── cli-json-output/              # Worktree directory (ignored)
│   └── (CLI modifications)
│
├── lambda/                       # ✅ Tracked - Lambda functions
├── terraform/                    # ✅ Tracked - Infrastructure
└── docs/                         # ✅ Tracked - Documentation
```

---

## Review Checklist

- [ ] Navigate to `react-frontend/frontend`
- [ ] Run `npm install`
- [ ] Verify `.env` has `VITE_DEV_MODE=true` (for auth bypass)
- [ ] Run `npm run dev`
- [ ] Open http://localhost:5173
- [ ] Should go directly to dashboard (no login required)
- [ ] Explore dashboard, videos, notes, credits pages
- [ ] Test with `VITE_DEV_MODE=false` to see login flow
- [ ] Check API integration with backend
- [ ] Review code structure in `src/`
- [ ] Decide what to do with orphaned `frontend/Dockerfile`

---

## Next Steps After Review

1. **If frontend looks good**:
   - Merge `feature/react-frontend` into `develop`
   - Add Dockerfile to proper location
   - Update CI/CD pipeline for frontend deployment
   - Delete orphaned `frontend/` directory

2. **If changes needed**:
   - Make changes in the worktree
   - Commit to `feature/react-frontend` branch
   - Push updates

3. **For Obsidian integration**:
   - See `docs/OBSIDIAN-CLONE-INTEGRATION.md`
   - Provide details about your Obsidian clone for specific integration code
