#!/usr/bin/env python3
"""Test Tor with yt-dlp fallback."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from yt_study_buddy.video_processor import VideoProcessor
from loguru import logger

# Test videos (using the same one known to have English subtitles)
videos = [
    "dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
]

processor = VideoProcessor("tor")

logger.warning("Testing Tor with YT-DLP fallback...")
logger.info("="*50)

for video_id in videos:
    logger.info(f"\nTesting: {video_id}")
    try:
        result = processor.get_transcript(video_id)
        method = result.get('method', 'tor')
        logger.success(f"✓ Success via {method} ({result['length']} chars)")
    except Exception as e:
        logger.error(f"✗ Failed: {e}")

logger.info("\n" + "="*50)
processor.provider.print_stats()
