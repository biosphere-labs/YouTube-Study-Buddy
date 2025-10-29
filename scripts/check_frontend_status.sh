#!/bin/bash
cd /home/justin/Documents/dev/workspaces/ytstudybuddy

echo "=== Checking if frontend/ is tracked by git ==="
git ls-files frontend/ | wc -l

echo -e "\n=== Checking git status for frontend/ ==="
git status frontend/

echo -e "\n=== Checking .gitignore for frontend ==="
grep -n "frontend" .gitignore

echo -e "\n=== If frontend is not tracked, add it now ==="
if [ $(git ls-files frontend/ | wc -l) -eq 0 ]; then
    echo "Frontend is NOT tracked. Adding it now..."
    git add -f frontend/
    git status
    echo "Ready to commit. Run:"
    echo "  git commit -m 'fix: Add frontend directory to git tracking'"
else
    echo "Frontend IS tracked ($(git ls-files frontend/ | wc -l) files)"
fi
