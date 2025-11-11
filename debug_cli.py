#!/usr/bin/env python3
"""
Debug wrapper for CLI - easily debug any CLI command with LangSmith tracing.

Usage:
    1. Set LANGSMITH_API_KEY in .env (optional, for LangSmith tracing)
    2. Edit ENABLE_LANGSMITH and CLI_ARGS below
    3. Set breakpoints in any file (cli.py, langgraph_workflow.py, etc.)
    4. Right-click this file → Debug 'debug_cli'
    5. View traces at: https://smith.langchain.com/

Examples of CLI_ARGS:
    ['https://youtube.com/watch?v=dQw4w9WgXcQ']
    ['--parallel', '--workers', '3', '--file', 'urls.txt']
    ['--subject', 'Python', 'https://youtube.com/watch?v=xyz']
    ['--help']
"""
import sys
import os
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from yt_study_buddy.cli import main

# ============================================================
# EDIT THIS SECTION TO TEST DIFFERENT CLI COMMANDS
# ============================================================

# Enable LangSmith tracing (requires LANGSMITH_API_KEY in .env)
ENABLE_LANGSMITH = True
LANGSMITH_PROJECT = "youtube-study-buddy-debug"

CLI_ARGS = [
    '--debug-logging',
    'https://youtu.be/2VauS2awvMw',
]

def setup_langsmith_tracing():
    """
    Enable LangSmith tracing for LangGraph workflows.

    Requires LANGSMITH_API_KEY in .env file.
    Get your API key from: https://smith.langchain.com/settings
    """
    if not ENABLE_LANGSMITH:
        return

    api_key = os.getenv('LANGSMITH_API_KEY')
    if not api_key:
        print("⚠️  LangSmith tracing disabled: LANGSMITH_API_KEY not found in .env")
        print("   Get your API key from: https://smith.langchain.com/settings")
        print()
        return

    # Enable LangSmith tracing
    os.environ['LANGCHAIN_TRACING_V2'] = 'true'
    os.environ['LANGCHAIN_PROJECT'] = LANGSMITH_PROJECT
    os.environ['LANGCHAIN_API_KEY'] = api_key

    print("=" * 60)
    print("✓ LangSmith Tracing ENABLED")
    print(f"  Project: {LANGSMITH_PROJECT}")
    print(f"  View traces at: https://smith.langchain.com/")
    print("=" * 60)
    print()


def debug_with_args(args):
    """
    Run the CLI with specified arguments.

    This simulates: uv run yt-study-buddy <args>

    With LangSmith enabled, you'll see:
    - Node execution traces
    - State changes at each node
    - Timing information
    - Error traces with full context
    """
    # Setup LangSmith tracing
    setup_langsmith_tracing()

    print("=" * 60)
    print("DEBUG MODE - CLI Arguments:")
    print(f"  {' '.join(args)}")
    print("=" * 60)
    print()

    # Set sys.argv to simulate CLI execution
    sys.argv = ['yt-study-buddy'] + args

    # Run the CLI (set breakpoints in cli.py or other files)
    main()


if __name__ == '__main__':
    debug_with_args(CLI_ARGS)
