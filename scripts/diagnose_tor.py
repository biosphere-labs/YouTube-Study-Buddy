#!/usr/bin/env python3
"""
Diagnose Tor exit node issues.

Tests Tor connection, checks exit IPs, and verifies YouTube accessibility.
"""
import requests
import time
from stem import Signal
from stem.control import Controller
from loguru import logger

def get_tor_session():
    """Create a session that routes through Tor."""
    session = requests.Session()
    session.proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    return session

def get_exit_ip(session):
    """Get current Tor exit IP."""
    try:
        response = session.get('https://api.ipify.org?format=json', timeout=10)
        return response.json()['ip']
    except Exception as e:
        return f"Error: {e}"

def rotate_circuit(controller):
    """Request new Tor circuit."""
    controller.signal(Signal.NEWNYM)
    # Tor enforces a 10-second cooldown between NEWNYM signals
    # Wait 11 seconds to ensure we get a new circuit
    time.sleep(11)

def test_youtube_access(session, exit_ip):
    """Test if YouTube allows requests from this exit IP."""
    try:
        # Try to fetch YouTube transcript API
        url = "https://www.youtube.com/api/timedtext?v=dQw4w9WgXcQ&lang=en"
        response = session.get(url, timeout=10)

        if response.status_code == 200:
            return "✓ ALLOWED"
        elif response.status_code == 429:
            return "✗ RATE LIMITED (429)"
        elif response.status_code == 403:
            return "✗ BLOCKED (403)"
        else:
            return f"? STATUS {response.status_code}"
    except requests.exceptions.Timeout:
        return "✗ TIMEOUT"
    except Exception as e:
        return f"✗ ERROR: {str(e)[:50]}"

def main():
    logger.info("🔍 TOR EXIT NODE DIAGNOSTICS")
    logger.info("="*70)


    # Test Tor connection
    logger.info("1. Testing Tor connection...")
    session = get_tor_session()

    try:
        exit_ip = get_exit_ip(session)
        logger.success(f"   ✓ Tor is working")
        logger.debug(f"   Current exit IP: {exit_ip}")
    except Exception as e:
        logger.error(f"   ✗ Tor connection failed: {e}")
        logger.info("\nMake sure Tor is running:")
        logger.info("  sudo systemctl start tor")
        return



    # Test current exit node with YouTube
    logger.info("2. Testing current exit node with YouTube...")
    status = test_youtube_access(session, exit_ip)
    logger.info(f"   {exit_ip}: {status}")


    # Test multiple exit nodes
    logger.info("3. Testing 10 random exit nodes...")
    logger.info(f"   (Rotating circuits and testing YouTube access)")


    try:
        # Connect to Tor control port
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()

            results = []

            for i in range(10):
                logger.info(f"   Test {i+1}/10...", end=" ", flush=True)

                # Rotate circuit
                rotate_circuit(controller)

                # Get new exit IP
                exit_ip = get_exit_ip(session)

                # Test YouTube
                status = test_youtube_access(session, exit_ip)

                results.append((exit_ip, status))
                logger.info(f"{exit_ip} - {status}")

                time.sleep(1)  # Brief pause between tests

        
            logger.info("="*70)
            logger.info("RESULTS SUMMARY")
            logger.info("="*70)

            allowed = sum(1 for _, s in results if "ALLOWED" in s)
            blocked = sum(1 for _, s in results if "BLOCKED" in s or "RATE LIMITED" in s)
            timeout = sum(1 for _, s in results if "TIMEOUT" in s)
            other = len(results) - allowed - blocked - timeout

            logger.success(f"✓ Allowed:      {allowed}/10 ({allowed*10}%)")
            logger.error(f"✗ Blocked:      {blocked}/10 ({blocked*10}%)")
            logger.info(f"⏱ Timeouts:     {timeout}/10 ({timeout*10}%)")
            logger.info(f"? Other:        {other}/10 ({other*10}%)")
        

            if allowed == 0:
                logger.warning("⚠️  WARNING: None of the 10 exit nodes could access YouTube!")
            
                logger.info("POSSIBLE CAUSES:")
                logger.info("1. YouTube is blocking all Tor exit nodes from your region")
                logger.info("2. Your IP range is globally blacklisted")
                logger.info("3. Aggressive rate limiting is in effect")
            
                logger.info("SOLUTIONS:")
                logger.info("1. Wait 1-2 hours and try again")
                logger.debug("2. Use fewer parallel workers (reduce simultaneous requests)")
                logger.info("3. Increase delays between requests")
                logger.info("4. Consider VPN + Tor double proxy (advanced)")
                logger.warning("5. Use yt-dlp fallback method instead")
            elif allowed < 3:
                logger.warning("⚠️  LOW SUCCESS RATE")
            
                logger.info("Many Tor exits are blocked. Recommendations:")
                logger.warning("1. Increase retry interval to 30+ minutes")
                logger.debug("2. Reduce parallel workers to 1-2")
                logger.info("3. Add longer delays between retries")
            else:
                logger.success("✓ Good diversity! Some exits work.")
            
                logger.info("Recommendations:")
                logger.warning("1. Keep retrying - you'll eventually get working exits")
                logger.warning("2. Use 15-minute retry interval")
                logger.warning("3. Consider running retry in watch mode")

    except Exception as e:
        logger.error(f"\n✗ Error connecting to Tor control port: {e}")
        logger.info("\nMake sure Tor control port is configured:")
        logger.info("  1. Edit /etc/tor/torrc")
        logger.info("  2. Add: ControlPort 9051")
        logger.info("  3. Add: CookieAuthentication 0")
        logger.info("  4. Restart: sudo systemctl restart tor")

if __name__ == '__main__':
    main()
