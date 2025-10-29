#!/usr/bin/env python3
"""
Fix existing notes that have escaped newline characters.
This script will replace literal \n\n with actual newlines.
"""

import os
import sys
from pathlib import Path
from loguru import logger

def fix_note_file(filepath):
    """Fix a single note file by replacing escaped newlines."""
    logger.debug(f"Processing: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if file has the issue (literal \n characters)
        if '\\n' in content:
            logger.info(f"  Found escaped newlines, fixing...")

            # Replace escaped newlines with actual newlines
            fixed_content = content.replace('\\n\\n', '\n\n').replace('\\n', '\n')

            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)

            logger.success(f"  ✓ Fixed")
            return True
        else:
            logger.info(f"  No issues found")
            return False

    except Exception as e:
        logger.error(f"  ERROR: {e}")
        return False


def main():
    """Fix all markdown files in the notes directory."""
    notes_dir = Path("notes")

    if not notes_dir.exists():
        logger.error(f"ERROR: Directory '{notes_dir}' not found")
        sys.exit(1)

    logger.info(f"Scanning {notes_dir} for markdown files...\n")

    fixed_count = 0
    total_count = 0

    # Process all .md files in notes directory and subdirectories
    for md_file in notes_dir.rglob("*.md"):
        total_count += 1
        if fix_note_file(md_file):
            fixed_count += 1

    logger.info(f"\n{'='*50}")
    logger.info(f"Processed {total_count} files")
    logger.info(f"Fixed {fixed_count} files")
    logger.info(f"{'='*50}")


if __name__ == "__main__":
    main()
