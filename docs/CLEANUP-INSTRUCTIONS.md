# Cleanup Instructions for ytstudybuddy Repository

## What Has Been Completed

✅ **Merged react-frontend branch into develop**
   - React frontend code is now on develop branch
   - All frontend files are in `frontend/` directory on develop
   - Merge commit: bf9f4d0

✅ **Removed react-frontend worktree**
   - Worktree directory removed
   - No longer appears in `git worktree list`

✅ **Updated .gitignore**
   - Removed obsolete worktree entries
   - Only keeps `cli-json-output/` if it exists

## What Still Needs to Be Done

### 1. Delete cli-json-output Branch

The `feature/cli-json-output` branch appears to be outdated (only has "wip" commit) and removes files that were added more recently.

**Local:**
```bash
cd /home/justin/Documents/dev/workspaces/ytstudybuddy
git branch -D feature/cli-json-output
```

**Remote:**
```bash
git push origin --delete feature/cli-json-output
```

### 2. Remove Orphaned Directories

**frontend/** - Contains only orphaned Dockerfile (771 bytes)
```bash
rm -rf frontend/
```

**webapp/** - Contains old planning documents
```bash
rm -rf webapp/
```

### 3. Update .gitignore

Remove the cli-json-output line since we're deleting that worktree:

Edit `.gitignore` and remove:
```
# Feature branch worktrees (code is on feature branches, these are just working directories)
# cli-json-output/ - Code is on feature/cli-json-output branch
cli-json-output/
```

### 4. Verify Clean Status

```bash
git status
```

Should show clean working tree.

### 5. Push to Remote

```bash
git push origin develop
```

## Complete Cleanup Script

Run this from the repository root:

```bash
cd /home/justin/Documents/dev/workspaces/ytstudybuddy

# Remove orphaned directories
rm -rf frontend/
rm -rf webapp/

# Delete cli-json-output branch
git branch -D feature/cli-json-output
git push origin --delete feature/cli-json-output

# Update .gitignore to remove cli-json-output entry
cat > .gitignore << 'EOF'
# Environment files
.env
.env.*.local

# IDE
.vscode
.idea/

# Project specific
docs/
scripts/
urls.txt
test_urls.txt
/autofix.log
notes/
sessions/
!sessions/README.md
debug_logs/
data/
CLAUDE.md

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Node.js / Electron
node_modules/
package-lock.json
dist-electron/
*.AppImage
*.deb
*.dmg
*.exe
*.msi
EOF

# Commit the gitignore cleanup
git add .gitignore
git commit -m "chore: Clean up .gitignore after worktree removal"

# Verify status
git status

# Push to remote
git push origin develop
```

## Summary of Changes

| Item | Action | Reason |
|------|--------|--------|
| `feature/react-frontend` | ✅ Merged into develop | Frontend code is production-ready |
| `react-frontend/` worktree | ✅ Removed | No longer needed after merge |
| `feature/cli-json-output` | ❌ Delete | Outdated "wip" branch |
| `frontend/` directory | ❌ Delete | Orphaned Dockerfile only |
| `webapp/` directory | ❌ Delete | Old planning documents |
| `.gitignore` | ❌ Clean up | Remove references to deleted worktrees |

## Final Repository Structure

After cleanup, the develop branch will contain:

```
ytstudybuddy/
├── frontend/                  # ✅ React app (from merged branch)
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── lambda/                    # ✅ Lambda functions
├── lambda-layer/              # ✅ Lambda layer
├── terraform/                 # ✅ Infrastructure
├── src/                       # ✅ Python CLI source
├── tests/                     # ✅ Tests
├── docker/                    # ✅ Docker configs
├── .github/workflows/         # ✅ CI/CD
└── docs/                      # ✅ Documentation
```

No more worktree directories cluttering the root!
