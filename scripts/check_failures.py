#!/usr/bin/env python3
"""
Quick failure analysis script - shows why videos are failing.
"""
import json
from pathlib import Path
from datetime import datetime
from collections import Counter
from loguru import logger

def analyze_failures():
    """Analyze processing log for failure patterns."""
    log_path = Path("notes/processing_log.json")

    if not log_path.exists():
        logger.debug("❌ No processing log found (notes/processing_log.json)")
        return

    with open(log_path, 'r') as f:
        jobs = json.load(f)

    if not jobs:
        logger.info("📝 Log is empty - no videos processed yet")
        return

    # Stats
    total = len(jobs)
    failed = [j for j in jobs if not j.get('success')]
    succeeded = [j for j in jobs if j.get('success')]

    logger.debug(f"\n📊 PROCESSING STATISTICS")
    logger.info(f"=" * 60)
    logger.info(f"Total jobs:      {total}")
    logger.success(f"✅ Successful:    {len(succeeded)} ({len(succeeded)/total*100:.1f}%)")
    logger.error(f"❌ Failed:        {len(failed)} ({len(failed)/total*100:.1f}%)")

    if succeeded:
        methods = Counter(j.get('method', 'unknown') for j in succeeded)
        logger.success(f"\n✓ Success by method:")
        for method, count in methods.most_common():
            logger.info(f"  • {method}: {count}")

        avg_duration = sum(j.get('processing_duration', 0) for j in succeeded) / len(succeeded)
        logger.info(f"\n⏱  Average duration: {avg_duration:.1f}s")

    if not failed:
        logger.info(f"\n✅ All jobs succeeded!")
        return

    # Analyze failures
    logger.error(f"\n❌ FAILURE ANALYSIS")
    logger.info(f"=" * 60)

    # Error types
    error_types = Counter()
    for job in failed:
        error = job.get('error', 'Unknown error')
        # Categorize errors
        if 'blocking' in error.lower() or 'ip' in error.lower():
            error_types['YouTube IP Block'] += 1
        elif 'transcript' in error.lower() or 'subtitle' in error.lower():
            error_types['No Transcript Available'] += 1
        elif 'timeout' in error.lower():
            error_types['Timeout'] += 1
        elif 'connection' in error.lower():
            error_types['Connection Error'] += 1
        else:
            error_types['Other'] += 1

    logger.error("Error categories:")
    for error_type, count in error_types.most_common():
        logger.error(f"  • {error_type}: {count}")

    # Show sample failures
    logger.error(f"\n📋 Recent Failures (last 5):")
    for job in failed[-5:]:
        video_id = job.get('video_id', 'unknown')
        error = job.get('error', 'Unknown')
        duration = job.get('processing_duration', 0)
        timestamp = job.get('logged_at', 'unknown')[:19]

        logger.info(f"\n  Video: {video_id}")
        logger.info(f"  Time: {timestamp}")
        logger.info(f"  Duration: {duration:.1f}s")
        logger.error(f"  Error: {error[:100]}...")

    # Recommendations
    logger.info(f"\n💡 RECOMMENDATIONS")
    logger.info(f"=" * 60)

    if error_types.get('YouTube IP Block', 0) > 0:
        logger.warning("⚠️  YouTube is blocking Tor exit nodes")
        logger.info("   Solutions:")
        logger.info("   1. Wait a few minutes between requests")
        logger.info("   2. Rotate Tor circuit: sudo systemctl restart tor")
        logger.debug("   3. Use fewer parallel workers")
        logger.info("   4. Enable circuit rotation (check Tor control port)")

    if error_types.get('No Transcript Available', 0) > 0:
        logger.warning("⚠️  Some videos don't have transcripts/subtitles")
        logger.info("   This is expected - not all videos have captions")

    if error_types.get('Timeout', 0) > 0:
        logger.warning("⚠️  Timeouts occurring")
        logger.info("   Solutions:")
        logger.info("   1. Increase timeout in settings")
        logger.info("   2. Check internet connection")
        logger.info("   3. Try at different time of day")

def check_exit_nodes():
    """Check exit node tracker status."""
    log_path = Path("notes/exit_nodes.json")

    logger.info(f"\n🌐 EXIT NODE STATUS")
    logger.info(f"=" * 60)

    if not log_path.exists():
        logger.info("📝 No exit nodes tracked yet")
        logger.info("   (Will be created after first Tor use)")
        return

    with open(log_path, 'r') as f:
        nodes = json.load(f)

    if not nodes:
        logger.info("📝 No exit nodes tracked yet")
        return

    now = datetime.now()
    in_cooldown = []
    available = []

    for ip, data in nodes.items():
        try:
            last_used = datetime.fromisoformat(data['last_used'])
            elapsed = (now - last_used).total_seconds()

            if elapsed < 3600:  # 1 hour
                remaining = 3600 - elapsed
                in_cooldown.append((ip, data, remaining))
            else:
                available.append((ip, data))
        except:
            pass

    logger.info(f"Total tracked:   {len(nodes)}")
    logger.info(f"⏳ In cooldown:   {len(in_cooldown)} (can't reuse yet)")
    logger.info(f"✅ Available:     {len(available)} (ready to use)")

    if in_cooldown:
        logger.info(f"\n⏳ Nodes in cooldown (most recent):")
        for ip, data, remaining in sorted(in_cooldown, key=lambda x: x[2])[:5]:
            minutes = int(remaining / 60)
            use_count = data.get('use_count', 0)
            logger.info(f"  • {ip}: {minutes}m remaining ({use_count} uses)")

    if available:
        logger.info(f"\n✅ Available nodes (most recent):")
        sorted_available = sorted(available, key=lambda x: x[1].get('last_used', ''), reverse=True)
        for ip, data in sorted_available[:5]:
            last_used = data.get('last_used', 'N/A')[:19]
            use_count = data.get('use_count', 0)
            logger.info(f"  • {ip}: {use_count} uses, last: {last_used}")

def show_current_exit():
    """Show currently active Tor exit node."""
    import subprocess
    try:
        result = subprocess.run(
            ['curl', '--socks5', 'localhost:9050', 'https://api.ipify.org'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            ip = result.stdout.strip()
            logger.info(f"\n🔄 Current Tor Exit: {ip}")
            return ip
        else:
            logger.error(f"\n⚠️  Could not check current Tor exit")
    except Exception as e:
        logger.error(f"\n⚠️  Error checking Tor exit: {e}")
    return None

if __name__ == "__main__":
    logger.info("\n" + "=" * 60)
    logger.error("  📊 YouTube Study Buddy - Failure Analysis")
    logger.info("=" * 60)

    analyze_failures()
    check_exit_nodes()
    show_current_exit()

    logger.info("\n" + "=" * 60)
    logger.info("\n💡 Tip: Open Streamlit app and check the 'Logs' tab")
    logger.info("   for interactive filtering and detailed views!")
    logger.info("\n" + "=" * 60 + "\n")
