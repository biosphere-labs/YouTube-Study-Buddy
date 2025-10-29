#!/usr/bin/env python3
"""
Diagnostic script to test transcript fetching and identify failure points.
"""
import sys
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from yt_study_buddy.tor_transcript_fetcher import TorTranscriptFetcher
from yt_study_buddy.video_processor import VideoProcessor

def test_tor_connection():
    """Test if Tor proxy is working."""
    logger.info("=" * 60)
    logger.info("1. Testing Tor Connection")
    logger.info("=" * 60)

    fetcher = TorTranscriptFetcher()

    if fetcher.check_tor_connection():
        logger.success("✓ Tor proxy is working!")
        return True
    else:
        logger.error("✗ Tor proxy NOT working")
        return False

def test_video_title(video_id: str):
    """Test fetching video title."""
    logger.info("\n" + "=" * 60)
    logger.info(f"2. Testing Video Title Fetch for {video_id}")
    logger.info("=" * 60)

    processor = VideoProcessor(provider_type='tor')
    title = processor.get_video_title(video_id)

    logger.info(f"Title: {title}")

    if title and not title.startswith("Video_"):
        logger.success("✓ Title fetch successful")
        return True
    else:
        logger.error("✗ Title fetch failed (using fallback)")
        return False

def test_transcript_fetch(video_id: str):
    """Test fetching transcript."""
    logger.info("\n" + "=" * 60)
    logger.info(f"3. Testing Transcript Fetch for {video_id}")
    logger.info("=" * 60)

    fetcher = TorTranscriptFetcher()

    # Try with fallback
    result = fetcher.fetch_with_fallback(video_id)

    if result:
        logger.success(f"✓ Transcript fetched successfully!")
        logger.info(f"  Method: {result.get('method', 'unknown')}")
        logger.info(f"  Length: {result.get('length', 0)} characters")
        logger.info(f"  Duration: {result.get('duration', 'unknown')}")
        return True, result
    else:
        logger.error("✗ Transcript fetch failed (both Tor and yt-dlp)")
        return False, None

def analyze_common_failures():
    """Analyze common failure patterns."""
    logger.info("\n" + "=" * 60)
    logger.error("4. Common Failure Analysis")
    logger.info("=" * 60)

    logger.debug("\nChecking processing_log.json...")
    log_path = Path("notes/processing_log.json")

    if not log_path.exists():
        logger.error("✗ processing_log.json doesn't exist yet")
        return

    import json
    try:
        with open(log_path, 'r') as f:
            jobs = json.load(f)

        if not jobs:
            logger.error("✗ No jobs logged yet")
            return

        failed = [j for j in jobs if not j.get('success')]

        logger.info(f"\nTotal jobs: {len(jobs)}")
        logger.error(f"Failed jobs: {len(failed)}")

        if failed:
            logger.error("\nFailure reasons:")
            error_counts = {}
            for job in failed:
                error = job.get('error', 'Unknown error')
                error_type = error.split(':')[0] if ':' in error else error
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

            for error_type, count in sorted(error_counts.items(), key=lambda x: -x[1]):
                logger.error(f"  • {error_type}: {count} occurrences")

            # Show a sample failure
            logger.error(f"\nSample failure details:")
            sample = failed[0]
            logger.info(f"  Video ID: {sample.get('video_id')}")
            logger.error(f"  Error: {sample.get('error')}")
            logger.debug(f"  Duration: {sample.get('processing_duration', 0):.1f}s")

    except Exception as e:
        logger.error(f"✗ Error reading log: {e}")

def check_exit_nodes():
    """Check exit node tracker."""
    logger.info("\n" + "=" * 60)
    logger.info("5. Exit Node Tracker Status")
    logger.info("=" * 60)

    log_path = Path("notes/exit_nodes.json")

    if not log_path.exists():
        logger.error("✗ exit_nodes.json doesn't exist yet")
        logger.info("  (This is created on first Tor use)")
        return

    import json
    from datetime import datetime

    try:
        with open(log_path, 'r') as f:
            nodes = json.load(f)

        logger.info(f"Total tracked nodes: {len(nodes)}")

        if not nodes:
            logger.info("  (No nodes tracked yet)")
            return

        now = datetime.now()
        in_cooldown = 0
        available = 0

        for ip, data in nodes.items():
            try:
                last_used = datetime.fromisoformat(data['last_used'])
                elapsed = (now - last_used).total_seconds()

                if elapsed < 3600:
                    in_cooldown += 1
                else:
                    available += 1
            except:
                pass

        logger.info(f"In cooldown: {in_cooldown}")
        logger.info(f"Available: {available}")

        # Show most recently used
        sorted_nodes = sorted(
            nodes.items(),
            key=lambda x: x[1].get('last_used', ''),
            reverse=True
        )

        logger.info(f"\nMost recently used nodes:")
        for ip, data in sorted_nodes[:5]:
            last_used = data.get('last_used', 'N/A')[:19]
            use_count = data.get('use_count', 0)
            logger.info(f"  • {ip}: {use_count} uses, last: {last_used}")

    except Exception as e:
        logger.error(f"✗ Error reading exit nodes: {e}")

def main():
    """Run all diagnostics."""
    logger.info("\n🔍 YouTube Study Buddy - Diagnostic Tool\n")

    # Test with a known working video
    test_video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up

    # Run tests
    tor_ok = test_tor_connection()

    if not tor_ok:
        logger.warning("\n⚠️  WARNING: Tor proxy not working!")
        logger.info("   Start Tor with: sudo systemctl start tor")
        logger.info("   Or use Docker: docker-compose up -d")
        return

    title_ok = test_video_title(test_video_id)
    transcript_ok, transcript_data = test_transcript_fetch(test_video_id)

    # Analyze existing failures
    analyze_common_failures()
    check_exit_nodes()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    logger.error(f"Tor Connection:     {'✓ OK' if tor_ok else '✗ FAILED'}")
    logger.warning(f"Title Fetch:        {'✓ OK' if title_ok else '⚠ DEGRADED'}")
    logger.error(f"Transcript Fetch:   {'✓ OK' if transcript_ok else '✗ FAILED'}")

    if transcript_ok and transcript_data:
        method = transcript_data.get('method', 'unknown')
        if method == 'tor':
            logger.success("\n✓ Everything working with Tor!")
        elif method == 'yt-dlp':
            logger.error("\n⚠ Tor failed, but yt-dlp fallback worked")
        else:
            logger.warning(f"\n⚠ Working but method unknown: {method}")
    elif not transcript_ok:
        logger.error("\n✗ CRITICAL: Cannot fetch transcripts!")
        logger.info("   Check:")
        logger.info("   1. Is YouTube accessible?")
        logger.info("   2. Is Tor working? (test manually)")
        logger.info("   3. Try a different video ID")

    logger.info("\n" + "=" * 60)

if __name__ == "__main__":
    main()
