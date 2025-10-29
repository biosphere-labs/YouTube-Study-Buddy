# Frontend Separation Guide

## Quick Start

To separate the frontend into its own repository, run this single command:

```bash
cd /home/justin/Documents/dev/workspaces/ytstudybuddy
bash create_frontend_repo.sh
```

This will automatically:
1. ✅ Create new `YouTube-Study-Buddy-Frontend` directory
2. ✅ Copy all frontend code
3. ✅ Copy relevant documentation
4. ✅ Create comprehensive README
5. ✅ Set up .gitignore
6. ✅ Initialize git repository
7. ✅ Make initial commit

## What Gets Created

### New Repository Structure

```
/home/justin/Documents/dev/workspaces/YouTube-Study-Buddy-Frontend/
├── frontend/                          # Complete React application
│   ├── src/                           # All source code
│   ├── public/                        # Static assets
│   ├── .env.example                   # Environment template
│   ├── package.json                   # Dependencies
│   ├── vite.config.ts                 # Vite configuration
│   ├── DEV-MODE.md                    # Dev mode documentation
│   ├── TAILWIND-V4-MIGRATION.md       # Tailwind v4 guide
│   └── Dockerfile                     # Docker configuration
├── docs/
│   ├── DEPLOYMENT.md                  # Deployment guide
│   └── OBSIDIAN-CLONE-INTEGRATION.md  # Obsidian integration guide
├── README.md                          # Comprehensive frontend README
└── .gitignore                         # Git ignore rules
```

### Documentation Created

1. **README.md** - Complete frontend documentation:
   - Tech stack overview
   - Project structure
   - Getting started guide
   - Configuration details
   - Deployment options
   - Troubleshooting
   - Backend integration

2. **docs/DEPLOYMENT.md** - Deployment guide for:
   - AWS S3 + CloudFront
   - Netlify
   - Vercel
   - Docker
   - Environment configuration
   - Post-deployment testing

3. **docs/OBSIDIAN-CLONE-INTEGRATION.md** - Obsidian integration guide (copied from main repo)

## After Running the Script

### 1. Verify the New Repository

```bash
cd /home/justin/Documents/dev/workspaces/YouTube-Study-Buddy-Frontend

# Check files were copied
ls -la frontend/

# Check git status
git status

# View commit
git log
```

### 2. Test the Frontend Builds

```bash
cd frontend
npm install
npm run build
```

Should complete without errors.

### 3. Test Development Server

```bash
npm run dev
```

Should start on http://localhost:5173

### 4. Create GitHub Repository

1. Go to https://github.com/new
2. Name: `YouTube-Study-Buddy-Frontend`
3. Description: "React TypeScript frontend for YouTube Study Buddy"
4. Keep it public or private as needed
5. **Don't initialize with README** (we already have one)

### 5. Push to GitHub

```bash
cd /home/justin/Documents/dev/workspaces/YouTube-Study-Buddy-Frontend

# Add remote
git remote add origin git@github.com:YOUR-USERNAME/YouTube-Study-Buddy-Frontend.git

# Push
git push -u origin main
```

### 6. Clean Up Main Repository

```bash
cd /home/justin/Documents/dev/workspaces/ytstudybuddy

# Remove frontend directory
rm -rf frontend/

# Remove webapp planning docs
rm -rf webapp/

# Remove frontend-specific docs (now in frontend repo)
rm -f docs/OBSIDIAN-CLONE-INTEGRATION.md

# Commit the cleanup
git add -A
git commit -m "chore: Remove frontend code (moved to separate repository)

Frontend moved to YouTube-Study-Buddy-Frontend repository:
- https://github.com/YOUR-USERNAME/YouTube-Study-Buddy-Frontend

See docs/FRONTEND-REPOSITORY.md for details on the separation
and how to work with both repositories."

# Push to remote
git push origin develop
```

## What Remains in Main Repository

The main `ytstudybuddy` repository will contain:

```
ytstudybuddy/
├── src/                   # Python CLI source code
├── lambda/                # AWS Lambda functions
├── lambda-layer/          # Lambda layer with dependencies
├── terraform/             # Infrastructure as Code
├── tests/                 # Backend tests
├── docker/                # Docker configurations
├── .github/workflows/     # CI/CD for backend
├── docs/                  # Backend documentation
│   ├── FRONTEND-REPOSITORY.md        # Frontend repo info (NEW)
│   ├── SERVERLESS-*.md               # Backend deployment docs
│   └── ...
├── streamlit_app.py       # Streamlit web interface
├── pyproject.toml         # Python dependencies
└── README.md              # Backend README (to be updated)
```

## Updating README Files

### Main Repository README

Add this section to `/home/justin/Documents/dev/workspaces/ytstudybuddy/README.md`:

```markdown
## Frontend

The web frontend is maintained in a separate repository for independent development and deployment:

**[YouTube-Study-Buddy-Frontend](https://github.com/YOUR-USERNAME/YouTube-Study-Buddy-Frontend)**

The frontend is a modern React TypeScript application with:
- AWS Cognito authentication
- Dashboard, videos, notes, and credits management
- Real-time progress tracking
- Tailwind CSS 4 + shadcn/ui

See the frontend repository for setup and deployment instructions.
```

### Frontend Repository README

The script automatically creates a comprehensive README. After pushing to GitHub, update the backend repository link:

Edit `YouTube-Study-Buddy-Frontend/README.md` and update:
```markdown
## Backend Integration

This frontend connects to the YouTube Study Buddy backend API:
- **Repository**: [YouTube-Study-Buddy](https://github.com/YOUR-USERNAME/YouTube-Study-Buddy)
- **API Documentation**: See backend repository
```

## Environment Variables

### Frontend (.env in frontend repo)

```bash
# Backend API
VITE_API_GATEWAY_URL=https://your-api-gateway-url

# AWS Cognito
VITE_COGNITO_USER_POOL_ID=us-east-1_xxx
VITE_COGNITO_CLIENT_ID=xxx
VITE_COGNITO_REGION=us-east-1

# Stripe
VITE_STRIPE_PUBLIC_KEY=pk_xxx

# Development
VITE_DEV_MODE=true  # Set to false for production
VITE_ENABLE_ANALYTICS=false
```

### Backend (stays in main repo)

Your existing backend configuration remains unchanged.

## CI/CD Workflows

### Frontend CI/CD (in frontend repo)

Create `.github/workflows/deploy-frontend.yml`:

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main, develop]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install and build
        run: |
          cd frontend
          npm ci
          npm run build
      - name: Deploy to S3
        # Add your deployment steps
```

### Backend CI/CD (in main repo)

Your existing `.github/workflows/deploy.yml` remains, but remove frontend-related steps.

## Development Workflow

### Working on Frontend

```bash
cd /home/justin/Documents/dev/workspaces/YouTube-Study-Buddy-Frontend
git checkout -b feature/my-feature
# Make changes
cd frontend && npm run dev
# Test changes
git commit -m "feat: Add my feature"
git push origin feature/my-feature
# Create PR on GitHub
```

### Working on Backend

```bash
cd /home/justin/Documents/dev/workspaces/ytstudybuddy
git checkout -b feature/my-feature
# Make changes
uv run streamlit run streamlit_app.py
# Test changes
git commit -m "feat: Add my feature"
git push origin feature/my-feature
# Create PR on GitHub
```

## Testing Full Stack

1. **Start Backend** (choose one):
   ```bash
   # Local Streamlit
   cd ytstudybuddy
   uv run streamlit run streamlit_app.py

   # Or use deployed Lambda API
   ```

2. **Configure Frontend**:
   ```bash
   cd YouTube-Study-Buddy-Frontend/frontend
   # Edit .env with backend URL
   VITE_API_GATEWAY_URL=http://localhost:8501  # or your API Gateway URL
   ```

3. **Start Frontend**:
   ```bash
   npm run dev
   ```

4. **Test Integration**:
   - Login/authentication
   - Submit video
   - View notes
   - Check credits

## Troubleshooting

### Script fails to run

```bash
# Make sure script is executable
chmod +x create_frontend_repo.sh

# Run with explicit bash
bash create_frontend_repo.sh

# Check for errors
bash -x create_frontend_repo.sh
```

### Frontend files not copied

Check that the `frontend/` directory exists in the main repo:
```bash
ls -la /home/justin/Documents/dev/workspaces/ytstudybuddy/frontend/
```

### Git commit fails

Make sure git is configured:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Cannot push to GitHub

Make sure you have SSH keys set up:
```bash
ssh -T git@github.com
```

Or use HTTPS instead:
```bash
git remote set-url origin https://github.com/YOUR-USERNAME/YouTube-Study-Buddy-Frontend.git
```

## Benefits of This Separation

✅ **Independent Development**: Frontend and backend teams work in parallel
✅ **Faster CI/CD**: Smaller repos = faster builds and deployments
✅ **Clear Ownership**: Each repo has clear responsibility
✅ **Flexible Deployment**: Deploy frontend without touching backend
✅ **Better Organization**: Cleaner, more focused repositories
✅ **Technology Freedom**: Upgrade or replace either stack independently

## Next Steps

1. ✅ Run `create_frontend_repo.sh`
2. ✅ Test frontend builds and runs
3. ✅ Create GitHub repository
4. ✅ Push to GitHub
5. ✅ Clean up main repository
6. ✅ Update README files
7. ✅ Set up CI/CD for frontend
8. ✅ Test full stack integration
9. ✅ Update documentation
10. ✅ Celebrate! 🎉

## Questions?

- **Frontend issues**: See `YouTube-Study-Buddy-Frontend` repository
- **Backend issues**: See `ytstudybuddy` repository
- **Integration**: See `docs/FRONTEND-REPOSITORY.md` in main repo

---

**Summary**: Just run `bash create_frontend_repo.sh` and follow the steps above!
