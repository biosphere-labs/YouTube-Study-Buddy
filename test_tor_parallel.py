"""
Test script for the new Tor parallel processing architecture.

Tests TorIPQueue + RotatingTorClient integration without processing actual videos.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from yt_study_buddy.rotating_tor_client import RotatingTorClient
from yt_study_buddy.tor_ip_queue import TorIPQueue
from loguru import logger


def test_ip_queue_allocation():
    """Test that TorIPQueue can pre-allocate unique IPs."""
    logger.info("\n" + "="*60)
    logger.info("TEST: TorIPQueue Pre-allocation")
    logger.info("="*60)

    try:
        # Create rotating client
        client = RotatingTorClient(
            tor_host='127.0.0.1',
            tor_port=9050,
            control_port=9051,
            cooldown_hours=1.0,
            max_rotation_attempts=5
        )

        # Test 1: Pre-allocate 3 unique IPs
        logger.info("\nTest 1: Allocating 3 unique IPs...")
        queue = TorIPQueue(client, target_size=3, queue_timeout=120)
        queue.start(blocking=True, timeout=120)

        # Verify all IPs were allocated
        stats = queue.get_stats()
        logger.info(f"\nQueue Stats:")
        logger.info(f"  Target size: {stats['target_size']}")
        logger.info(f"  Allocated: {stats['allocated']}")
        logger.info(f"  Failed attempts: {stats['failed_attempts']}")
        logger.info(f"  Queue size: {stats['queue_size']}")
        logger.info(f"  Allocation complete: {stats['allocation_complete']}")

        assert stats['allocated'] == 3, f"Expected 3 IPs, got {stats['allocated']}"
        assert stats['queue_size'] == 3, f"Expected queue size 3, got {stats['queue_size']}"

        # Test 2: Pull IPs from queue
        logger.info("\nTest 2: Pulling IPs from queue...")
        pulled_ips = []
        for i in range(3):
            exit_ip, session, proxies = queue.get_next_connection(worker_id=i)
            pulled_ips.append(exit_ip)
            logger.success(f"  Worker {i}: Pulled IP {exit_ip}")

            # Verify session is configured correctly
            assert 'socks5' in proxies['http'], "Session not configured with Tor proxy"
            assert session is not None, "Session is None"

        # Test 3: Verify all IPs are unique
        logger.info("\nTest 3: Verifying IP uniqueness...")
        unique_ips = set(pulled_ips)
        logger.info(f"  Total IPs: {len(pulled_ips)}")
        logger.info(f"  Unique IPs: {len(unique_ips)}")
        logger.info(f"  IPs: {pulled_ips}")

        assert len(unique_ips) == 3, f"IPs are not unique! {pulled_ips}"

        # Cleanup
        queue.stop()

        logger.success("\n✓ All tests passed!")
        return True

    except Exception as e:
        logger.error(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fetcher_with_preconfig():
    """Test that TorTranscriptFetcher works with pre-configured session."""
    logger.info("\n" + "="*60)
    logger.info("TEST: TorTranscriptFetcher with Pre-configured Session")
    logger.info("="*60)

    try:
        from yt_study_buddy.tor_transcript_fetcher import TorTranscriptFetcher
        import requests

        # Create a pre-configured session
        session = requests.Session()
        proxies = {
            'http': 'socks5://127.0.0.1:9050',
            'https': 'socks5://127.0.0.1:9050'
        }
        session.proxies = proxies
        exit_ip = "test.ip.1.2"

        # Test 1: Create fetcher with pre-config
        logger.info("\nTest 1: Creating fetcher with pre-configured session...")
        fetcher = TorTranscriptFetcher(
            session=session,
            proxies=proxies,
            exit_ip=exit_ip
        )

        # Verify configuration
        assert fetcher._using_preconfig == True, "Fetcher should be using pre-config"
        assert fetcher.exit_ip == exit_ip, f"Exit IP mismatch: {fetcher.exit_ip} != {exit_ip}"
        assert fetcher.session == session, "Session not set correctly"

        logger.success("  ✓ Fetcher configured correctly")

        # Test 2: Verify rotation is skipped
        logger.info("\nTest 2: Verifying rotation is skipped for pre-configured fetcher...")
        result = fetcher.rotate_tor_circuit()
        assert result == False, "Rotation should return False (skipped)"
        logger.success("  ✓ Rotation correctly skipped")

        # Test 3: Create fetcher without pre-config (legacy)
        logger.info("\nTest 3: Creating fetcher without pre-config (legacy mode)...")
        legacy_fetcher = TorTranscriptFetcher()
        assert legacy_fetcher._using_preconfig == False, "Legacy fetcher should not be using pre-config"
        assert legacy_fetcher.exit_ip is None, "Legacy fetcher should have no pre-configured exit IP"
        logger.success("  ✓ Legacy mode works")

        logger.success("\n✓ All tests passed!")
        return True

    except Exception as e:
        logger.error(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("\n" + "="*60)
    logger.info("TOR PARALLEL PROCESSING ARCHITECTURE TESTS")
    logger.info("="*60)

    # Check if Tor is running
    logger.info("\nChecking Tor connection...")
    try:
        import requests
        response = requests.get(
            'https://api.ipify.org',
            proxies={'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'},
            timeout=10
        )
        tor_ip = response.text
        logger.success(f"✓ Tor is running (Exit IP: {tor_ip})")
    except Exception as e:
        logger.error(f"✗ Tor is not running or not accessible: {e}")
        logger.error("Please start Tor: docker-compose up -d tor-proxy")
        return False

    # Run tests
    results = []

    # Test 1: TorIPQueue allocation
    results.append(test_ip_queue_allocation())

    # Test 2: TorTranscriptFetcher with pre-config
    results.append(test_fetcher_with_preconfig())

    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    passed = sum(results)
    total = len(results)
    logger.info(f"Passed: {passed}/{total}")

    if passed == total:
        logger.success("✓ All tests passed!")
        return True
    else:
        logger.error(f"✗ {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
