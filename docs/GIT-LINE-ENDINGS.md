# Git Line Endings Configuration

## Problem

Git was showing warnings on Ubuntu/Linux:
```
warning: in the working copy of 'file.md', CRLF will be replaced by LF the next time Git touches it
```

This happens when Git thinks it should convert line endings, even though we're on Linux where LF (Unix) line endings are standard.

## Solution Applied

### Global Configuration (All Repositories)

Set these Git configuration options globally:

```bash
git config --global core.autocrlf false
git config --global core.eol lf
```

**Explanation:**
- `core.autocrlf false` - Don't automatically convert line endings
- `core.eol lf` - Use LF (Unix/Linux) line endings by default

### Local Configuration (Per Repository)

Also set for each repository:

```bash
git config core.autocrlf false
git config core.eol lf
```

### .gitattributes File

Created `.gitattributes` file in both repositories to enforce LF line endings:

**Main Repository:**
```gitattributes
# Set default behavior - normalize all text files to LF (Linux/Unix standard)
* text=auto eol=lf

# Explicit file types
*.sh text eol=lf
*.py text eol=lf
*.js text eol=lf
*.ts text eol=lf
*.md text eol=lf
*.yml text eol=lf
# ... etc

# Binary files
*.png binary
*.jpg binary
*.pdf binary
# ... etc
```

**Frontend Repository:**
Same structure with frontend-specific file types (tsx, jsx, css, etc.)

## Why This Happened

Git's `core.autocrlf` was likely set to `true` or `input`, which causes:
- `true` - Convert LF to CRLF on checkout, CRLF to LF on commit (Windows behavior)
- `input` - Convert CRLF to LF on commit only
- `false` - Don't convert anything (Linux/Mac default)

Since we're on Ubuntu (Linux), we want `false` with `eol=lf`.

## How to Verify Configuration

Check global settings:
```bash
git config --global --get core.autocrlf
git config --global --get core.eol
```

Check local repo settings:
```bash
git config --get core.autocrlf
git config --get core.eol
```

Check .gitattributes:
```bash
cat .gitattributes
```

## Expected Output

- `core.autocrlf` = `false`
- `core.eol` = `lf`
- `.gitattributes` exists with `* text=auto eol=lf`

## What Changed

**Committed to both repositories:**
1. Updated `.gitattributes` to enforce LF line endings
2. Set local Git config for each repository
3. Set global Git config for all future repositories

**Main repo commit:** 040f6b0
**Frontend repo commit:** a92c2ad

## No More Warnings

You should no longer see the CRLF/LF conversion warnings when:
- Committing files
- Checking out branches
- Running git status

## Cross-Platform Teams

If you work with Windows users, they should set:
```bash
git config --global core.autocrlf true
```

This way:
- Windows users get CRLF in their working directory
- Linux/Mac users get LF in their working directory
- Repository always stores LF (via .gitattributes)

## Testing

Create a new file and check line endings:
```bash
echo "test" > test.txt
git add test.txt
git commit -m "test"
# Should not show any warnings

# Check file line endings
file test.txt
# Should show: ASCII text
# Not: ASCII text, with CRLF line terminators
```

## References

- [Git Documentation: core.autocrlf](https://git-scm.com/docs/git-config#Documentation/git-config.txt-coreautocrlf)
- [Git Documentation: core.eol](https://git-scm.com/docs/git-config#Documentation/git-config.txt-coreeol)
- [Git Attributes](https://git-scm.com/docs/gitattributes)

## Summary

✅ Global config set to `autocrlf=false`, `eol=lf`
✅ Local configs set for both repositories
✅ `.gitattributes` added to both repositories
✅ Committed and pushed changes
✅ No more line ending warnings on Linux
