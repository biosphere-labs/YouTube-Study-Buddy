#!/bin/bash
# Commit the frontend separation preparation files

cd /home/justin/Documents/dev/workspaces/ytstudybuddy

echo "Committing frontend separation preparation files..."

git add START-HERE.md
git add FRONTEND-SEPARATION-GUIDE.md
git add create_frontend_repo.sh
git add docs/FRONTEND-REPOSITORY.md

git commit -m "docs: Add frontend repository separation tools and documentation

Prepare for moving frontend to separate YouTube-Study-Buddy-Frontend repository:
- create_frontend_repo.sh: Automated script to create frontend repo
- START-HERE.md: Quick start guide
- FRONTEND-SEPARATION-GUIDE.md: Comprehensive step-by-step guide
- docs/FRONTEND-REPOSITORY.md: Integration and workflow documentation

Run 'bash create_frontend_repo.sh' to create the separate frontend repository."

git push origin develop

echo "✅ Files committed and pushed"
