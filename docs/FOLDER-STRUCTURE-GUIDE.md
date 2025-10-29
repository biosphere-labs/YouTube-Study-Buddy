# Folder Structure Guide - YT Study Buddy

## Overview

This project uses **git worktrees** for parallel development. This guide explains what each directory contains, what's tracked vs ignored, and how to access code for review.

## Quick Answer: How to Review the React Frontend

The React frontend code is tracked on the `feature/react-frontend` branch. Here are three ways to access it:

### Option 1: Use the Existing Worktree (Fastest)
```bash
cd react-frontend/frontend
ls -la src/  # View the source code
```

### Option 2: Checkout the Branch
```bash
# From main worktree
git checkout feature/react-frontend
cd frontend/
ls -la src/
```

### Option 3: View on Remote
```bash
git log feature/react-frontend --oneline  # See commits
# Or view on GitHub at the feature/react-frontend branch
```

### How to Run Locally
```bash
cd react-frontend/frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## Folder Structure Diagram

```
ytstudybuddy/                          # Main worktree (develop branch)
├── .gitignore                         # Ignores worktree directories below
├── lambda/                            # ✅ TRACKED - Lambda function code
├── terraform/                         # ✅ TRACKED - Infrastructure definitions
├── docs/                              # ✅ TRACKED - Documentation
├── streamlit_app.py                   # ✅ TRACKED - Streamlit web interface
│
├── react-frontend/                    # 🚫 IGNORED - Worktree directory
│   │                                  # Contains full repo checkout on feature/react-frontend
│   ├── lambda/                        # (duplicate of main worktree)
│   ├── terraform/                     # (duplicate of main worktree)
│   └── frontend/                      # ⭐ THE ACTUAL REACT CODE ⭐
│       ├── src/
│       ├── package.json
│       └── vite.config.ts
│
├── cli-json-output/                   # 🚫 IGNORED - Worktree directory
│   │                                  # Contains full repo checkout on feature/cli-json-output
│   └── (CLI modifications for JSON output support)
│
└── frontend/                          # ❓ Mystery directory - only contains Dockerfile
    └── Dockerfile                     # (771 bytes, unclear purpose)
```

---

## Understanding Git Worktrees

### What are Worktrees?

Git worktrees allow multiple working directories for different branches in the same repository. Instead of switching branches and changing files, you have separate directories checked out to different branches simultaneously.

### Active Worktrees

```bash
$ git worktree list
/home/justin/Documents/dev/workspaces/ytstudybuddy                  fb13bdb [develop]
/home/justin/Documents/dev/workspaces/ytstudybuddy/cli-json-output  5571fa4 [feature/cli-json-output]
/home/justin/Documents/dev/workspaces/ytstudybuddy/react-frontend   e645850 [feature/react-frontend]
```

### Why Worktrees Were Used

During parallel development, we needed to:
1. Keep `develop` branch clean and stable
2. Work on React frontend in isolation (`feature/react-frontend`)
3. Work on CLI JSON output simultaneously (`feature/cli-json-output`)
4. Avoid constant branch switching

---

## What's Tracked vs Ignored

### ✅ Tracked in Git (on appropriate branches)

| Code | Branch | Location |
|------|--------|----------|
| Lambda functions | `develop` | `lambda/` in main worktree |
| Terraform infra | `develop` | `terraform/` in main worktree |
| React frontend | `feature/react-frontend` | Tracked on branch (viewed in `react-frontend/frontend/`) |
| CLI JSON output | `feature/cli-json-output` | Tracked on branch (viewed in `cli-json-output/`) |

### 🚫 Ignored in Git

The **worktree directories themselves** are ignored in `.gitignore`:

```bash
# Feature branch worktrees (code is on feature branches, these are just working directories)
# react-frontend/ - Code is on feature/react-frontend branch
# cli-json-output/ - Code is on feature/cli-json-output branch
cli-json-output/
react-frontend/
```

**Why?** Because these directories are just working checkouts. The code is tracked on their respective branches, not in these directories on the `develop` branch.

---

## Detailed Directory Breakdown

### `react-frontend/`
- **Type**: Git worktree directory
- **Status**: Ignored by git (on develop branch)
- **Branch**: `feature/react-frontend`
- **Purpose**: Separate working directory for React frontend development
- **Contains**:
  - Full repository checkout at feature/react-frontend branch
  - **Actual React code** in `react-frontend/frontend/` subdirectory
- **Commits**:
  ```
  e645850 chore: Add worktree directories to .gitignore with explanation
  3c923a0 feat(frontend): Update for serverless architecture with API Gateway and Cognito
  49163e7 feat(frontend): Add React frontend with auth, dashboard, videos, and notes
  ```

### `cli-json-output/`
- **Type**: Git worktree directory
- **Status**: Ignored by git (on develop branch)
- **Branch**: `feature/cli-json-output`
- **Purpose**: Modifications to CLI for JSON output support
- **Contains**: Full repository checkout with CLI changes

### `frontend/`
- **Type**: Regular directory (NOT a worktree)
- **Status**: ❓ Unclear - likely leftover from earlier development
- **Contains**: Only a Dockerfile (771 bytes)
- **Recommendation**: Can likely be deleted or should be clarified

### `lambda/`
- **Type**: Regular directory
- **Status**: ✅ Tracked on develop branch
- **Purpose**: AWS Lambda function handlers for serverless architecture
- **Contains**:
  - `analyze/` - AI analysis Lambda
  - `notes/` - Notes CRUD operations
  - `search/` - Search functionality
  - `shared/` - Common utilities
  - And more...

### `terraform/`
- **Type**: Regular directory
- **Status**: ✅ Tracked on develop branch
- **Purpose**: Infrastructure as Code for AWS deployment
- **Contains**:
  - `modules/` - Reusable Terraform modules
  - `environments/` - Environment-specific configs
  - Lambda, API Gateway, DynamoDB, S3, Cognito definitions

---

## Verification Commands

### Check What's on Each Branch

```bash
# See React frontend commits
git log feature/react-frontend --oneline

# See CLI JSON commits
git log feature/cli-json-output --oneline

# See develop branch commits
git log develop --oneline
```

### Verify Code Exists

```bash
# React frontend code
ls -la react-frontend/frontend/src/

# CLI JSON output changes
ls -la cli-json-output/

# Lambda functions (on develop)
ls -la lambda/
```

### Check What's Ignored

```bash
cat .gitignore | grep -A3 "worktrees"
```

---

## How to Work with This Structure

### Reviewing the React Frontend

1. **Navigate to the worktree**:
   ```bash
   cd react-frontend/frontend
   ```

2. **View the code**:
   ```bash
   ls -la src/
   cat src/main.tsx
   ```

3. **Run it locally**:
   ```bash
   npm install
   npm run dev
   ```

4. **Check dependencies**:
   ```bash
   cat package.json
   ```

### Making Changes to React Frontend

If you're in the worktree:
```bash
cd react-frontend/frontend
# Make changes
git add .
git commit -m "feat: Your changes"
git push origin feature/react-frontend
```

If you prefer to checkout the branch:
```bash
# From main worktree
git checkout feature/react-frontend
cd frontend/
# Make changes
git add .
git commit -m "feat: Your changes"
```

### Merging Frontend into Develop

When the React frontend is ready:
```bash
# From main worktree
git checkout develop
git merge feature/react-frontend
git push origin develop
```

---

## Why This Matters

### The Confusion

Multiple ignored directories made it unclear:
- Where the actual code lives
- How to access it for review
- What's tracked vs what's just a working directory

### The Reality

- **Code IS tracked** - on feature branches
- **Directories are ignored** - they're just checkouts
- **Worktrees enable parallel work** - without branch switching

### The Solution

This guide provides:
- Clear structure diagram
- Access instructions for each codebase
- Verification commands
- Workflow guidance

---

## Next Steps

1. **Review the React frontend** using the instructions above
2. **Clarify the `frontend/` directory** - what is it for?
3. **Consider merging** feature branches when ready
4. **Update deployment** to include React frontend in CI/CD

## Questions?

- Why are there duplicate directories in worktrees? **Because worktrees contain full repo checkouts**
- Where is the React code actually tracked? **On the `feature/react-frontend` branch**
- Can I delete worktree directories? **Yes, but you'll lose any uncommitted changes in them**
- How do I clean up worktrees? **`git worktree remove <directory>`**
