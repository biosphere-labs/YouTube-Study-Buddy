# Frontend Repository Information

## Overview

The YouTube Study Buddy frontend has been separated into its own repository for independent development and deployment.

## Frontend Repository

**Repository Name**: `YouTube-Study-Buddy-Frontend`
**Location**: `/home/justin/Documents/dev/workspaces/YouTube-Study-Buddy-Frontend`
**GitHub**: *[To be created]*

## Why Separated?

1. **Independent Development Cycles**: Frontend and backend can be developed, tested, and deployed independently
2. **Different Tech Stacks**: React/TypeScript frontend vs Python backend
3. **Simplified CI/CD**: Separate pipelines for frontend and backend deployments
4. **Clear Separation of Concerns**: Better project organization
5. **Team Workflow**: Different teams can work on frontend/backend without conflicts

## Repository Structure

### Frontend Repository Contains:
- Complete React TypeScript application (`frontend/` directory)
- Frontend-specific documentation
- Deployment configurations for frontend
- Frontend CI/CD workflows
- Development mode and testing guides

### Main Repository Contains:
- Python CLI application
- Lambda functions for serverless backend
- Terraform infrastructure definitions
- Backend API documentation
- Integration tests
- Docker configurations for backend

## Setting Up the Frontend Repository

If you haven't created the separate repository yet, run:

```bash
cd /home/justin/Documents/dev/workspaces/ytstudybuddy
bash create_frontend_repo.sh
```

This will:
1. Create `YouTube-Study-Buddy-Frontend` directory
2. Copy all frontend code
3. Create comprehensive README and documentation
4. Set up proper .gitignore
5. Make initial git commit

## Connecting Frontend and Backend

### Backend API

The frontend connects to the backend via API Gateway:

```
Frontend (React) → API Gateway → Lambda Functions → DynamoDB/S3
```

### Environment Configuration

**Frontend `.env` file**:
```bash
VITE_API_GATEWAY_URL=https://your-api-gateway-url
VITE_COGNITO_USER_POOL_ID=us-east-1_xxx
VITE_COGNITO_CLIENT_ID=xxx
```

**Backend API Endpoints**:
- `GET /videos` - List videos
- `POST /videos` - Submit video for processing
- `GET /notes` - List generated notes
- `GET /credits/balance` - Check credit balance

See backend API documentation for full endpoint details.

## Development Workflow

### Frontend Development

```bash
cd /home/justin/Documents/dev/workspaces/YouTube-Study-Buddy-Frontend/frontend
npm install
npm run dev
```

Set `VITE_DEV_MODE=true` to bypass authentication during development.

### Backend Development

```bash
cd /home/justin/Documents/dev/workspaces/ytstudybuddy
# Run Streamlit app
uv run streamlit run streamlit_app.py

# Or deploy Lambda functions
cd terraform
terraform apply
```

### Full Stack Testing

1. Start backend (either local or deployed Lambda)
2. Update frontend `.env` with backend API URL
3. Start frontend dev server
4. Test integration

## Deployment

### Frontend Deployment

Deploy to:
- **AWS S3 + CloudFront** (recommended)
- **Netlify**
- **Vercel**
- **Docker container**

See `YouTube-Study-Buddy-Frontend/docs/DEPLOYMENT.md`

### Backend Deployment

Deploy to:
- **AWS Lambda** (serverless - recommended)
- **Docker + EC2**
- **ECS/Fargate**

See `docs/SERVERLESS-DEPLOYMENT.md` in this repository

## File Structure

### Before Separation
```
ytstudybuddy/
├── frontend/              # React app (was here)
├── lambda/                # Lambda functions
├── terraform/             # Infrastructure
└── src/                   # Python CLI
```

### After Separation
```
YouTube-Study-Buddy-Frontend/
└── frontend/              # React app (moved here)
    ├── src/
    ├── docs/
    └── README.md

ytstudybuddy/
├── lambda/                # Lambda functions
├── terraform/             # Infrastructure
├── src/                   # Python CLI
└── docs/                  # Backend docs
```

## Cleaning Up Main Repository

After creating the frontend repository, clean up the main repo:

```bash
cd /home/justin/Documents/dev/workspaces/ytstudybuddy

# Remove frontend directory from main repo
rm -rf frontend/
rm -rf webapp/  # Old planning docs

# Remove frontend-specific docs
rm -f docs/OBSIDIAN-CLONE-INTEGRATION.md  # Moved to frontend repo

# Commit cleanup
git add -A
git commit -m "chore: Remove frontend code (moved to separate repository)

Frontend has been moved to YouTube-Study-Buddy-Frontend repository
for independent development and deployment.

See docs/FRONTEND-REPOSITORY.md for details."

git push origin develop
```

## Shared Resources

Some resources may need to be duplicated between repositories:

### API Type Definitions
If TypeScript types are shared, consider:
- Creating a separate `@ytstudybuddy/types` npm package
- Duplicating type definitions (simpler for small projects)
- Using OpenAPI/Swagger to generate types from backend

### Documentation
- Architecture diagrams → Keep in main repo, reference from frontend
- API documentation → Keep in main repo, reference from frontend
- Frontend-specific docs → Move to frontend repo

### Configuration
- AWS credentials → Each repo has its own deployment
- Terraform state → Separate state for frontend resources
- Environment variables → Each repo has its own `.env.example`

## GitHub Setup

### Create Frontend Repository on GitHub

```bash
cd /home/justin/Documents/dev/workspaces/YouTube-Study-Buddy-Frontend

# Create repo on GitHub first, then:
git remote add origin git@github.com:your-username/YouTube-Study-Buddy-Frontend.git
git push -u origin main
```

### Repository Settings

**Main Repository**:
- Name: `YouTube-Study-Buddy`
- Description: "Backend API and infrastructure for YouTube Study Buddy"
- Topics: `python`, `aws-lambda`, `terraform`, `youtube`, `ai`

**Frontend Repository**:
- Name: `YouTube-Study-Buddy-Frontend`
- Description: "React TypeScript frontend for YouTube Study Buddy"
- Topics: `react`, `typescript`, `vite`, `tailwindcss`, `aws-cognito`

### Cross-Repository Links

Add to main repo README:
```markdown
## Frontend

The web frontend is in a separate repository:
- [YouTube-Study-Buddy-Frontend](https://github.com/your-username/YouTube-Study-Buddy-Frontend)
```

Add to frontend repo README:
```markdown
## Backend

The backend API is in a separate repository:
- [YouTube-Study-Buddy](https://github.com/your-username/YouTube-Study-Buddy)
```

## CI/CD Considerations

### Frontend CI/CD
- Build and test on every commit
- Deploy to staging on `develop` branch
- Deploy to production on `main` branch
- Run E2E tests against staging backend

### Backend CI/CD
- Run unit tests on every commit
- Deploy Lambda functions to staging
- Run integration tests
- Deploy to production with approval

### Integration Testing
Consider a third repository or use GitHub Actions workflows that:
- Trigger on either repo's changes
- Deploy both frontend and backend to test environment
- Run full integration tests
- Report results to both repositories

## Version Compatibility

Maintain compatibility matrix in both repositories:

| Frontend Version | Backend Version | Compatible |
|------------------|-----------------|------------|
| v1.0.x           | v1.0.x          | ✅         |
| v1.1.x           | v1.0.x          | ✅         |
| v2.0.x           | v2.0.x          | ✅         |

## Migration Checklist

- [ ] Run `create_frontend_repo.sh` to create new repository
- [ ] Verify all frontend files copied correctly
- [ ] Test frontend builds successfully (`npm run build`)
- [ ] Create GitHub repository for frontend
- [ ] Push frontend to GitHub
- [ ] Update README in both repositories with cross-links
- [ ] Clean up frontend from main repository
- [ ] Update CI/CD workflows in both repos
- [ ] Test full stack integration
- [ ] Update documentation

## Support

For questions about:
- **Frontend issues**: Open issue in `YouTube-Study-Buddy-Frontend` repo
- **Backend/API issues**: Open issue in `YouTube-Study-Buddy` repo
- **Integration issues**: Open issue in the relevant repo and cross-reference

## Benefits of Separation

✅ **Faster CI/CD**: Smaller repositories = faster builds
✅ **Clear ownership**: Frontend and backend teams work independently
✅ **Flexible deployment**: Deploy frontend and backend on different schedules
✅ **Better organization**: Clearer project structure
✅ **Easier onboarding**: New developers can focus on one repo
✅ **Technology flexibility**: Easier to migrate or upgrade either stack independently

## Challenges to Consider

⚠️ **API versioning**: Need clear API version compatibility
⚠️ **Shared types**: May need to duplicate or create shared package
⚠️ **Integration testing**: Requires coordination between repos
⚠️ **Documentation sync**: Keep docs in sync between repos

Overall, the benefits far outweigh the challenges for a project of this complexity.
