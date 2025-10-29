#!/bin/bash
# Cleanup script for ytstudybuddy repository

cd /home/justin/Documents/dev/workspaces/ytstudybuddy || exit 1

echo "=== Current Status ==="
git status

echo -e "\n=== Active Worktrees ==="
git worktree list

echo -e "\n=== Removing orphaned directories ==="

# Remove frontend/ directory (orphaned Dockerfile)
if [ -d "frontend" ]; then
    echo "Removing frontend/ directory..."
    rm -rf frontend/
    echo "✓ frontend/ removed"
fi

# Remove webapp/ directory (old planning docs)
if [ -d "webapp" ]; then
    echo "Removing webapp/ directory..."
    rm -rf webapp/
    echo "✓ webapp/ removed"
fi

# Delete cli-json-output branch if it exists
if git show-ref --verify --quiet refs/heads/feature/cli-json-output; then
    echo "Deleting feature/cli-json-output branch..."
    git branch -D feature/cli-json-output
    echo "✓ Branch deleted"
fi

# Delete remote cli-json-output branch if it exists
if git ls-remote --exit-code --heads origin feature/cli-json-output >/dev/null 2>&1; then
    echo "Deleting remote feature/cli-json-output branch..."
    git push origin --delete feature/cli-json-output
    echo "✓ Remote branch deleted"
fi

echo -e "\n=== Final Status ==="
git status

echo -e "\n=== Cleanup Complete ==="
