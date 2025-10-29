#!/usr/bin/env python3
"""Convert print statements to loguru logger calls based on context."""

import re
import sys
from pathlib import Path
from typing import List, Tuple

def determine_log_level(line: str) -> str:
    """Determine appropriate log level based on print content."""
    line_lower = line.lower()

    # ERROR level - highest priority
    if any(marker in line_lower for marker in [
        'error', 'failed', 'fail', '✗', 'could not', 'cannot',
        'exception', 'traceback', 'critical', 'fatal'
    ]):
        return 'error'

    # WARNING level
    if any(marker in line_lower for marker in [
        'warning', 'warn', '⚠', 'retrying', 'retry',
        'deprecated', 'fallback', 'skipping'
    ]):
        return 'warning'

    # SUCCESS level
    if any(marker in line_lower for marker in [
        '✓', 'success', 'acquired', 'released', 'rotated',
        'complete', 'finished', 'done'
    ]):
        return 'success'

    # DEBUG level
    if any(marker in line_lower for marker in [
        'debug', 'connection #', 'exit ip:', 'worker',
        'attempt', 'details', 'processing'
    ]):
        return 'debug'

    # Default to INFO
    return 'info'

def needs_loguru_import(content: str) -> bool:
    """Check if file already imports loguru."""
    return 'from loguru import logger' not in content and 'import loguru' not in content

def add_loguru_import(content: str) -> str:
    """Add loguru import after other imports."""
    lines = content.split('\n')

    # Find the last import statement
    last_import_idx = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            last_import_idx = i

    if last_import_idx >= 0:
        # Insert after last import
        lines.insert(last_import_idx + 1, 'from loguru import logger')
    else:
        # No imports found, add at top after docstring
        insert_idx = 0
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                else:
                    insert_idx = i + 1
                    break
        lines.insert(insert_idx, 'from loguru import logger')

    return '\n'.join(lines)

def convert_print_to_logger(content: str) -> Tuple[str, int]:
    """
    Convert print statements to logger calls.

    Returns:
        Tuple of (converted_content, num_replacements)
    """
    lines = content.split('\n')
    result_lines = []
    num_replacements = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # Match single-line print(f"...") or print("...")
        match = re.match(r'^(\s*)print\((.*)\)\s*$', line)

        if match:
            indent = match.group(1)
            print_content = match.group(2).strip()

            # Handle multi-line print statements
            # Check if line ends with incomplete parentheses
            if print_content.count('(') > print_content.count(')'):
                # Multi-line print, accumulate until closing paren
                full_content = print_content
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    full_content += ' ' + next_line
                    if full_content.count('(') == full_content.count(')'):
                        break
                    i += 1
                print_content = full_content.rstrip(')')

            # Determine log level
            log_level = determine_log_level(line)

            # Replace print with logger
            new_line = f'{indent}logger.{log_level}({print_content})'
            result_lines.append(new_line)
            num_replacements += 1
        else:
            result_lines.append(line)

        i += 1

    return '\n'.join(result_lines), num_replacements

def process_file(file_path: Path, dry_run: bool = False) -> Tuple[bool, int]:
    """
    Process a single Python file.

    Returns:
        Tuple of (modified, num_replacements)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"✗ Error reading {file_path}: {e}")
        return False, 0

    # Convert print statements
    new_content, num_replacements = convert_print_to_logger(content)

    if num_replacements == 0:
        return False, 0

    # Add loguru import if needed
    if needs_loguru_import(new_content):
        new_content = add_loguru_import(new_content)

    if dry_run:
        logger.info(f"  Would convert {num_replacements} print statements in {file_path}")
        return True, num_replacements

    # Write back
    try:
        file_path.write_text(new_content, encoding='utf-8')
        logger.success(f"  ✓ Converted {num_replacements} print statements in {file_path}")
        return True, num_replacements
    except Exception as e:
        logger.error(f"  ✗ Error writing {file_path}: {e}")
        return False, 0

def find_python_files(root_dir: Path, exclude_patterns: List[str] = None) -> List[Path]:
    """Find all Python files in directory tree."""
    if exclude_patterns is None:
        exclude_patterns = [
            '*/venv/*', '*/.venv/*', '*/env/*',
            '*/__pycache__/*', '*/.git/*',
            '*/build/*', '*/dist/*', '*/.pytest_cache/*',
            '*/node_modules/*', '*/.tox/*'
        ]

    python_files = []
    for py_file in root_dir.rglob('*.py'):
        # Check if file matches any exclude pattern
        if any(py_file.match(pattern) for pattern in exclude_patterns):
            continue
        python_files.append(py_file)

    return sorted(python_files)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert print statements to loguru logger calls across the codebase'
    )
    parser.add_argument(
        'paths',
        nargs='*',
        help='Specific files or directories to process (default: src/)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--exclude',
        nargs='+',
        help='Additional glob patterns to exclude'
    )

    args = parser.parse_args()

    # Determine root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Determine paths to process
    if args.paths:
        paths_to_process = [Path(p) for p in args.paths]
    else:
        paths_to_process = [project_root / 'src']

    logger.info("=" * 60)
    logger.info("Converting print statements to loguru logger calls")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("DRY RUN MODE - no files will be modified")

    # Collect all Python files
    all_files = []
    for path in paths_to_process:
        if path.is_file():
            all_files.append(path)
        elif path.is_dir():
            all_files.extend(find_python_files(path, args.exclude))
        else:
            logger.error(f"✗ Path not found: {path}")

    logger.info(f"\nFound {len(all_files)} Python files to process")

    # Process files
    total_modified = 0
    total_replacements = 0

    for file_path in all_files:
        modified, num_replacements = process_file(file_path, dry_run=args.dry_run)
        if modified:
            total_modified += 1
            total_replacements += num_replacements

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Files processed: {len(all_files)}")
    logger.info(f"Files modified: {total_modified}")
    logger.info(f"Total print statements converted: {total_replacements}")

    if args.dry_run:
        logger.info("\nRun without --dry-run to apply changes")
    else:
        logger.success("\n✓ Conversion complete!")

    logger.info("=" * 60)
