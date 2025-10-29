#!/usr/bin/env python3
"""Quick test script to debug transcript fetching."""

import sys
import os
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from yt_study_buddy.video_processor import VideoProcessor

# Test with multiple videos
test_urls = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley
    "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Gangnam Style
    "https://www.youtube.com/watch?v=kJQP7kiw5Fk",  # Luis Fonsi - Despacito
]

# Test both local Tor and environment-configured Tor
tor_configs = [
    {"name": "Local Tor (127.0.0.1:9050)", "tor_host": "127.0.0.1", "tor_port": 9050},
    {"name": "Env Tor (from TOR_HOST/TOR_PORT)", "tor_host": os.getenv('TOR_HOST', '127.0.0.1'), "tor_port": int(os.getenv('TOR_PORT', 9050))},
]

logger.info("=" * 80)
logger.info("TESTING TRANSCRIPT FETCHING WITH DIFFERENT TOR CONFIGURATIONS")
logger.info("=" * 80)

for config in tor_configs:
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Configuration: {config['name']}")
    logger.info(f"Tor Host: {config['tor_host']}, Tor Port: {config['tor_port']}")
    logger.info(f"{'=' * 80}\n")

    # Test first URL only with this config
    test_url = test_urls[0]

    try:
        processor = VideoProcessor(
            provider_type="tor",
            tor_host=config['tor_host'],
            tor_port=config['tor_port']
        )

        video_id = processor.get_video_id(test_url)
        logger.success(f"✓ Extracted video ID: {video_id}")

        logger.info(f"\nFetching transcript...")
        transcript_data = processor.get_transcript(video_id)
        logger.success(f"✓ Transcript fetched: {transcript_data['length']} characters")
        logger.success(f"✓ First 200 chars: {transcript_data['transcript'][:200]}...")

        logger.info(f"\nFetching title...")
        title = processor.get_video_title(video_id)
        logger.success(f"✓ Title: {title}")

        logger.info(f"\n✅ Configuration {config['name']} PASSED!")

    except Exception as e:
        logger.error(f"\n❌ Configuration {config['name']} FAILED!")
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        logger.info("\n" + "=" * 80)
        continue

logger.info("\n" + "=" * 80)
logger.success("TESTING COMPLETE - Testing multiple videos with working config")
logger.info("=" * 80)

# Now test multiple videos with the working config
logger.info("\nTesting 3 different videos with local Tor...")
for i, test_url in enumerate(test_urls, 1):
    logger.info(f"\n[{i}/{len(test_urls)}] Testing: {test_url}")
    logger.info("-" * 80)

    try:
        processor = VideoProcessor(provider_type="tor", tor_host="127.0.0.1", tor_port=9050)
        video_id = processor.get_video_id(test_url)
        logger.success(f"  ✓ Video ID: {video_id}")

        transcript_data = processor.get_transcript(video_id)
        logger.success(f"  ✓ Transcript: {transcript_data['length']} characters")

        title = processor.get_video_title(video_id)
        logger.success(f"  ✓ Title: {title[:60]}...")

        logger.info(f"  ✅ Video {i} PASSED!")

    except Exception as e:
        logger.error(f"  ❌ Video {i} FAILED: {e}")
        import traceback
        traceback.print_exc()

logger.info("\n" + "=" * 80)
logger.success("ALL TESTS COMPLETE")
logger.info("=" * 80)
