#!/bin/bash
set -e

cd /home/justin/Documents/dev/workspaces/ytstudybuddy

echo "=== Organizing Repository Files ==="

# Move markdown docs to docs/ (except README.md and CLAUDE.md)
echo "Moving markdown files to docs/..."
mv -v CLEANUP-INSTRUCTIONS.md docs/ 2>/dev/null || true
mv -v FIX-FRONTEND-TRACKING.md docs/ 2>/dev/null || true
mv -v SEPARATE-FRONTEND-REPO.md docs/ 2>/dev/null || true
mv -v FRONTEND-SEPARATION-GUIDE.md docs/ 2>/dev/null || true
mv -v START-HERE.md docs/ 2>/dev/null || true
mv -v RETRY_GUIDE.md docs/ 2>/dev/null || true
mv -v OBSIDIAN_LINKER_ANALYSIS.md docs/ 2>/dev/null || true

# Move scripts to scripts/ (keep docker scripts in root)
echo "Moving script files to scripts/..."
mkdir -p scripts
mv -v cleanup_script.sh scripts/ 2>/dev/null || true
mv -v check_frontend_status.sh scripts/ 2>/dev/null || true
mv -v create_frontend_repo.sh scripts/ 2>/dev/null || true
mv -v COMMIT-THESE-FILES.sh scripts/ 2>/dev/null || true
mv -v fix_line_endings.sh scripts/ 2>/dev/null || true
mv -v create_frontend_repo_simple.sh scripts/ 2>/dev/null || true

echo ""
echo "=== Adding files to git ==="
git add -f docs/
git add scripts/

echo ""
echo "=== Git Status ==="
git status

echo ""
echo "=== Ready to Commit ==="
echo "Files organized:"
echo "  - Markdown docs → docs/"
echo "  - Helper scripts → scripts/"
echo "  - Docker scripts stay in root"
echo ""
echo "Run this to commit:"
echo "  git commit -m 'chore: Organize documentation and scripts"
echo ""
echo "  - Move all markdown docs to docs/ folder"
echo "  - Move helper scripts to scripts/ folder"
echo "  - Keep Docker/deployment scripts in root"
echo "  - Prepare for frontend repository separation'"
