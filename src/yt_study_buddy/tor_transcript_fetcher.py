"""
Tor proxy-based transcript fetcher for YouTube videos.

Bypasses IP blocks by routing requests through Tor network.
"""
import random
import re
import socket
import time
from typing import Optional, List, Dict, Any

import requests
from loguru import logger
from stem import Signal, SocketError
from stem.control import Controller
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

from .ytdlp_fallback import YtDlpFallback
from .debug_logger import get_logger
from .exit_node_tracker import get_tracker
from .daily_exit_tracker import get_daily_tracker
from .error_classifier import simplify_error

class TorTranscriptFetcher:
    """Fetch YouTube transcripts through Tor proxy to avoid IP blocks."""

    def __init__(
        self,
        tor_host: str = '127.0.0.1',
        tor_port: int = 9050,
        tor_control_port: int = 9051,
        tor_control_password: Optional[str] = None
    ):
        """
        Initialize with Tor proxy settings.

        Args:
            tor_host: Tor SOCKS proxy host (default: localhost)
            tor_port: Tor SOCKS proxy port (default: 9050)
            tor_control_port: Tor control port for circuit rotation (default: 9051)
            tor_control_password: Password for Tor control port (default: None)
        """
        self.proxies = {
            'http': f'socks5://{tor_host}:{tor_port}',
            'https': f'socks5://{tor_host}:{tor_port}'
        }
        self.session = requests.Session()
        self.tor_host = tor_host
        self.tor_port = tor_port
        self.tor_control_port = tor_control_port
        self.tor_control_password = tor_control_password
        self.ytdlp_fallback = YtDlpFallback()

        # Track if control port is available (set to False after first failure)
        self._control_port_available = True

        # Daily exit node tracker
        self.daily_tracker = get_daily_tracker()

    def _record_attempt(self, video_id: str, attempt: int, success: bool, exit_ip: Optional[str] = None):
        """
        Record an attempt in the daily tracker.

        Args:
            video_id: YouTube video ID
            attempt: Attempt number (1-based)
            success: Whether the attempt succeeded
            exit_ip: Exit node IP (fetched if not provided)
        """
        if exit_ip is None:
            try:
                exit_ip = self.session.get(
                    'https://api.ipify.org',
                    proxies=self.proxies,
                    timeout=5
                ).text
            except:
                exit_ip = "unknown"

        self.daily_tracker.record_attempt(
            exit_ip=exit_ip,
            video_id=video_id,
            attempt=attempt,
            success=success
        )

    def rotate_tor_circuit(self, max_retries: int = 3, retry_delay: float = 2.0, max_rotation_attempts: int = 5) -> bool:
        """
        Request a new Tor circuit (new exit node) with retry logic.
        Avoids exit nodes that failed today.

        Args:
            max_retries: Maximum number of connection attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 2.0)
            max_rotation_attempts: Max attempts to get a non-failed exit IP (default: 5)

        Returns:
            True if circuit was rotated successfully, False otherwise
        """
        # Skip if we already know control port is unavailable
        if not self._control_port_available:
            return False

        # If coordination lock exists (parallel mode), acquire it for rotation
        # This prevents multiple workers from rotating the same Tor circuit simultaneously
        coordination_lock = getattr(self, '_coordination_lock', None)

        def _do_rotation():
            """Inner function that performs the actual rotation."""
            # Get list of IPs that failed today
            failed_ips = set(self.daily_tracker.get_failed_ips_today())
            if failed_ips:
                logger.debug(f"Avoiding {len(failed_ips)} failed IPs from today")

            for attempt in range(max_retries):
                try:
                    with Controller.from_port(
                        address=self.tor_host,
                        port=self.tor_control_port
                    ) as controller:
                        if self.tor_control_password:
                            controller.authenticate(password=self.tor_control_password)
                        else:
                            controller.authenticate()

                        # Try to get a non-failed exit node
                        rotation_attempts = 0
                        while rotation_attempts < max_rotation_attempts:
                            controller.signal(Signal.NEWNYM)

                            # CRITICAL: Close session to break persistent connections
                            # requests.Session() maintains connection pool that reuses same circuit
                            # Must create fresh connection to use new Tor circuit
                            self.session.close()
                            self.session = requests.Session()

                            # Wait for new circuit to be ready
                            # get_newnym_wait() is minimum, add buffer for circuit build time
                            wait_time = max(controller.get_newnym_wait(), 3.0)
                            time.sleep(wait_time)

                            # Check the new exit IP
                            try:
                                new_exit_ip = self.session.get(
                                    'https://api.ipify.org',
                                    proxies=self.proxies,
                                    timeout=5
                                ).text

                                # Check if this IP failed today
                                if new_exit_ip in failed_ips:
                                    rotation_attempts += 1
                                    logger.warning(f"⚠️  Got previously failed IP {new_exit_ip}, rotating again ({rotation_attempts}/{max_rotation_attempts})...")
                                    continue
                                else:
                                    logger.success(f"✓ Tor circuit rotated to new IP: {new_exit_ip}")
                                    return True

                            except Exception as ip_check_error:
                                logger.warning(f"⚠️  Could not verify exit IP: {ip_check_error}")
                                # Can't verify, but rotation succeeded
                                logger.success("✓ Tor circuit rotated (IP verification failed)")
                                return True

                        # Exhausted rotation attempts
                        logger.warning(f"⚠️  Could not find non-failed exit IP after {max_rotation_attempts} attempts")
                        return False

                except (ConnectionRefusedError, OSError, SocketError) as e:
                    # Connection errors - Tor might not be running yet or temporarily down
                    if attempt < max_retries - 1:
                        logger.info(f"Tor control port not ready (attempt {attempt + 1}/{max_retries})")
                        logger.warning(f"Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                    else:
                        # Mark control port as unavailable to stop future attempts
                        self._control_port_available = False
                        logger.warning(f"⚠️  Tor control port unavailable after {max_retries} attempts")
                        logger.info("Circuit rotation disabled - will use fixed exit nodes")

                except Exception as e:
                    # Authentication errors or other issues - don't retry
                    self._control_port_available = False
                    logger.error(f"⚠️  Tor circuit rotation failed: {type(e).__name__}")
                    logger.info("Circuit rotation disabled - will use fixed exit nodes")
                    return False

            return False

        # If we have a coordination lock (parallel mode), use it
        if coordination_lock is not None:
            with coordination_lock:
                logger.debug("  Acquired coordination lock for Tor rotation")
                return _do_rotation()
        else:
            # Sequential mode - no lock needed
            return _do_rotation()

    def check_tor_connection(self) -> bool:
        """
        Verify Tor is working by checking IP.

        Returns:
            True if Tor is working and IP is different, False otherwise
        """
        try:
            # Check IP without Tor
            normal_ip = requests.get('https://api.ipify.org', timeout=10).text

            # Check IP with Tor
            tor_ip = self.session.get(
                'https://api.ipify.org',
                proxies=self.proxies,
                timeout=10
            ).text

            logger.info(f"Normal IP: {normal_ip}")
            logger.info(f"Tor IP: {tor_ip}")

            return normal_ip != tor_ip
        except Exception as e:
            logger.error(f"Tor connection check failed: {e}")
            return False

    def check_transcript_availability(
        self,
        video_id: str,
        languages: List[str] = ['en']
    ) -> tuple[bool, Optional[str]]:
        """
        Quick check if transcript is available in requested languages.

        Args:
            video_id: YouTube video ID
            languages: List of language codes to check

        Returns:
            Tuple of (is_available, error_message)
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            # List available transcripts (fast operation)
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Check if any requested language is available
            for lang in languages:
                try:
                    transcript_list.find_transcript([lang])
                    return True, None
                except:
                    continue

            # Get available languages for error message
            available_langs = []
            for transcript in transcript_list:
                available_langs.append(transcript.language_code)

            if available_langs:
                return False, f"No transcript in {languages}, available: {available_langs[:5]}"
            else:
                return False, "No transcripts available for this video"

        except Exception as e:
            # If check fails, allow attempt (might still work)
            return True, None

    def fetch_transcript(
        self,
        video_id: str,
        languages: List[str] = ['en'],
        max_retries: int = 5,
        base_timeout: int = 60,
        max_timeout: int = 120,
        check_availability: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch transcript using Tor proxy with enhanced retry mechanism.

        Args:
            video_id: YouTube video ID
            languages: List of language codes to try (default: ['en'])
            max_retries: Maximum number of retry attempts (default: 5)
            base_timeout: Base timeout in seconds (default: 60)
            max_timeout: Maximum timeout in seconds (default: 120)
            check_availability: Quick check before fetching (default: True)

        Returns:
            Dictionary with transcript data or None if failed
        """
        # Quick availability check to fail fast
        if check_availability:
            is_available, error_msg = self.check_transcript_availability(video_id, languages)
            if not is_available:
                logger.error(f"⚠️  Transcript not available: {error_msg}")
                return None

        last_error = None

        for attempt in range(max_retries):
            try:
                # Rotate circuit on retries (not on first attempt)
                if attempt > 0:
                    logger.warning(f"Retry attempt {attempt + 1}/{max_retries}...")

                    # Try to rotate circuit, but don't fail if control port unavailable
                    rotation_success = self.rotate_tor_circuit()

                    # If circuit rotation failed, add extra delay to let rate limits expire
                    if not rotation_success:
                        extra_delay = 10 * attempt  # 10s, 20s, 30s, 40s...
                        logger.info(f"Circuit rotation unavailable, adding {extra_delay}s delay...")
                        time.sleep(extra_delay)

                    # Exponential backoff with jitter
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Waiting {backoff:.1f}s before retry...")
                    time.sleep(backoff)

                # Add random delay to appear more human-like
                time.sleep(random.uniform(1, 3))

                # Calculate adaptive timeout (increases with each retry)
                timeout = min(base_timeout * (1.5 ** attempt), max_timeout)
                logger.info(f"Using timeout: {timeout:.0f}s")

                # Use youtube-transcript-api with proxies
                # Note: youtube-transcript-api doesn't expose timeout directly,
                # but we set it on the session for requests made internally
                old_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(timeout)

                try:
                    # Instantiate API with Tor proxy configuration
                    proxy_config = GenericProxyConfig(
                        http_url=self.proxies['http'],
                        https_url=self.proxies['https']
                    )
                    api = YouTubeTranscriptApi(proxy_config=proxy_config)
                    fetched = api.fetch(video_id, languages=languages)
                    # Convert to list of snippets
                    transcript_list = list(fetched)
                except Exception as fetch_error:
                    attempt = attempt + 1
                    # Show exit node being used when fetch fails
                    try:
                        exit_ip = self.session.get(
                            'https://api.ipify.org',
                            proxies=self.proxies,
                            timeout=5
                        ).text
                        logger.error(f"✗ Fetch failed (attempt {attempt + 1}): {simplify_error(str(fetch_error))}")
                        logger.debug(f"   Exit IP: {exit_ip}")

                        # Record failure in daily tracker
                        self._record_attempt(video_id, attempt + 1, success=False, exit_ip=exit_ip)
                    except:
                        logger.error(f"✗ Fetch failed (attempt {attempt + 1}): {simplify_error(str(fetch_error))}")
                        logger.error(f"   Exit IP: Could not determine")

                        # Record failure with unknown IP
                        self._record_attempt(video_id, attempt + 1, success=False, exit_ip=None)
                    raise  # Re-raise to be caught by outer exception handlers
                finally:
                    socket.setdefaulttimeout(old_timeout)

                # Process transcript into the format expected by the app
                # FetchedTranscriptSnippet objects have .text attribute (not dict key)
                transcript_text = ' '.join([snippet.text for snippet in transcript_list])

                # Clean up the transcript
                transcript_text = re.sub(r'\s+', ' ', transcript_text)
                transcript_text = transcript_text.replace('[Music]', '').replace('[Applause]', '')
                logger.debug(f'transcript char len {len(transcript_text)}')
                # Calculate video duration
                duration_info = None
                if transcript_list:
                    last_snippet = transcript_list[-1]
                    duration_seconds = last_snippet.start + last_snippet.duration
                    duration_minutes = int(duration_seconds / 60)
                    duration_info = f"~{duration_minutes} minutes"

                # Show exit node on success and record
                try:
                    exit_ip = self.session.get(
                        'https://api.ipify.org',
                        proxies=self.proxies,
                        timeout=5
                    ).text
                    logger.success(f"✓ Successfully fetched transcript on attempt {attempt + 1} (Exit IP: {exit_ip})")

                    # Record success in daily tracker
                    self._record_attempt(video_id, attempt + 1, success=True, exit_ip=exit_ip)
                except:
                    logger.success(f"✓ Successfully fetched transcript on attempt {attempt + 1}")

                    # Record success with unknown IP
                    self._record_attempt(video_id, attempt + 1, success=True, exit_ip=None)

                # Save tracker after successful fetch
                self.daily_tracker.save()

                return {
                    'transcript': transcript_text,
                    'duration': duration_info,
                    'length': len(transcript_text),
                    'segments': transcript_list,  # Include raw segments for advanced use
                    'method': 'tor'  # Mark as Tor success
                }

            except (requests.exceptions.Timeout, socket.timeout) as e:
                last_error = e
                # Exit IP already logged by inner exception handler
                if attempt >= max_retries - 1:
                    logger.error(f"✗ All {max_retries} attempts timed out")

            except Exception as e:
                last_error = e
                # Exit IP already logged by inner exception handler
                if attempt >= max_retries - 1:
                    simplified = simplify_error(str(e))
                    logger.error(f"✗ All {max_retries} attempts failed")

        # Final error message
        if last_error:
            simplified_final = simplify_error(str(last_error))
            logger.error(f"Failed to fetch via Tor: {simplified_final}")

        # Save tracker after all attempts exhausted
        self.daily_tracker.save()

        return None

    def fetch_with_fallback(
        self,
        video_id: str,
        languages: List[str] = ['en']
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch transcript using Tor first, fall back to yt-dlp if Tor fails.

        Args:
            video_id: YouTube video ID
            languages: List of language codes

        Returns:
            Dictionary with transcript data or None if all methods failed
        """
        # Try Tor first (primary method)
        logger.info("Fetching transcript via Tor proxy...")
        result = self.fetch_transcript(video_id, languages)

        if result:
            logger.success("✓ Successfully fetched via Tor")
            # Ensure method is set
            if 'method' not in result:
                result['method'] = 'tor'
            return result
        else:
            logger.error("✗ Tor fetch failed")

            # Fall back to yt-dlp
            logger.info("Attempting yt-dlp fallback...")
            ytdlp_result = self.ytdlp_fallback.fetch_transcript(
                video_id, languages
            )

            if ytdlp_result:
                logger.success("✓ Successfully fetched via yt-dlp fallback")
                # Mark as yt-dlp method
                ytdlp_result['method'] = 'yt-dlp'
                return ytdlp_result
            else:
                logger.error("✗ YT-DLP fallback also failed")
                return None

    def get_video_title(
        self,
        video_id: str,
        max_retries: int = 3,
        timeout: int = 30,
        worker_id: Optional[int] = None,
        return_status: bool = False
    ) -> str | tuple[str, bool, Optional[str]]:
        """
        Get video title using YouTube oEmbed API through Tor with retry.

        Args:
            video_id: YouTube video ID
            max_retries: Maximum number of retry attempts (default: 3)
            timeout: Timeout in seconds per attempt (default: 30)
            worker_id: Optional worker ID for logging
            return_status: If True, returns (title, success, error_reason)

        Returns:
            If return_status=False: Video title (cleaned) or fallback Video_ID
            If return_status=True: Tuple of (title, success, error_reason)
        """
        logger = get_logger()
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        last_error = None
        last_response_data = None

        for attempt in range(max_retries):
            attempt_num = attempt + 1
            logger.log_title_fetch_attempt(video_id, attempt_num, max_retries, worker_id)

            try:
                if attempt > 0:
                    logger.warning(f"  Rotating circuit before retry {attempt_num}...")
                    self.rotate_tor_circuit()
                    backoff = (2 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(f"  Waiting {backoff:.1f}s before retry...")
                    time.sleep(backoff)

                response = self.session.get(
                    url,
                    proxies=self.proxies,
                    timeout=timeout * (1.5 ** attempt)
                )

                # Log response regardless of status
                response_data = None
                response_error = None

                try:
                    if response.status_code == 200:
                        response_data = response.json()
                        last_response_data = response_data
                    else:
                        response_error = f"HTTP {response.status_code}"
                        logger.error(f"  ✗ HTTP {response.status_code} response")
                except Exception as json_err:
                    response_error = f"JSON parse error: {json_err}"
                    logger.error(f"  ✗ Could not parse JSON: {json_err}")

                logger.log_api_response(
                    video_id=video_id,
                    url=url,
                    status_code=response.status_code,
                    response_data=response_data,
                    error=response_error,
                    worker_id=worker_id,
                    attempt=attempt_num
                )

                if response.status_code == 200 and response_data:
                    title = response_data.get('title')
                    if title:
                        # Clean title for filename
                        clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
                        result = clean_title[:100]

                        logger.log_title_result(
                            video_id=video_id,
                            title=result,
                            success=True,
                            total_attempts=attempt_num,
                            worker_id=worker_id
                        )
                        logger.success(f"  ✓ Title: {result}")

                        if return_status:
                            return result, True, None
                        return result
                    else:
                        logger.error(f"  ✗ No 'title' field in response")
                        logger.log_api_response(
                            video_id=video_id,
                            url=url,
                            status_code=200,
                            response_data=response_data,
                            error="No 'title' field in response",
                            worker_id=worker_id,
                            attempt=attempt_num
                        )

            except requests.exceptions.Timeout as e:
                last_error = e
                error_msg = f"Timeout after {timeout * (1.5 ** attempt):.1f}s"
                logger.error(f"  ✗ {error_msg}")
                logger.log_api_response(
                    video_id=video_id,
                    url=url,
                    status_code=0,
                    response_data=None,
                    error=error_msg,
                    worker_id=worker_id,
                    attempt=attempt_num
                )

            except Exception as e:
                last_error = e
                error_msg = str(e)
                logger.error(f"  ✗ Error: {error_msg}")
                logger.log_api_response(
                    video_id=video_id,
                    url=url,
                    status_code=0,
                    response_data=None,
                    error=error_msg,
                    worker_id=worker_id,
                    attempt=attempt_num
                )

        # All attempts failed
        fallback = f"Video_{video_id}"
        logger.error(f"  ✗ All {max_retries} attempts failed, using fallback: {fallback}")

        # Determine reason for failure
        error_reason = None
        if last_error:
            error_str = str(last_error)
            if 'timeout' in error_str.lower():
                error_reason = "Title fetch timeout"
            elif 'block' in error_str.lower() or '429' in error_str or '403' in error_str:
                error_reason = "YouTube blocking requests (rate limit or IP block)"
            elif 'connection' in error_str.lower():
                error_reason = "Connection error"
            else:
                error_reason = f"API error: {error_str[:50]}"
            logger.error(f"  Last error: {error_reason}")

        logger.log_title_result(
            video_id=video_id,
            title=fallback,
            success=False,
            total_attempts=max_retries,
            worker_id=worker_id
        )

        if return_status:
            return fallback, False, error_reason
        return fallback


# Usage examples
if __name__ == "__main__":
    import concurrent.futures

    # Example 1: Single fetcher (original usage)
    logger.info("=== Example 1: Single Fetcher ===")
    fetcher = TorTranscriptFetcher()

    if fetcher.check_tor_connection():
        logger.success("✓ Tor proxy is working!")

        video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
        transcript = fetcher.fetch_with_fallback(video_id)

        if transcript:
            logger.success(f"✓ Successfully fetched {len(transcript['segments'])} transcript segments")
            logger.info(f"Total length: {transcript['length']} characters")
            logger.info(f"Duration: {transcript['duration']}")
    else:
        logger.error("✗ Tor proxy not working. Check your setup.")
        logger.info(f"Make sure Tor is running on {fetcher.tor_host}:{fetcher.tor_port}")

    # Example 2: Pool with multiple workers (recommended for parallel processing)
    logger.debug("\n=== Example 2: Pool with Multiple Workers ===")
    logger.info("NOTE: For true unique exit nodes, you need either:")
    logger.info("  1. Multiple Tor instances on different ports, OR")
    logger.info("  2. Circuit rotation with enforcement_unique_exits=True (automatic)")

    # Create pool with 5 connections
    # This will enforce unique exit IPs by rotating circuits if needed
    pool = TorExitNodePool(
        pool_size=5,
        base_socks_port=9050,
        base_control_port=9051,
        enforce_unique_exits=True,  # Ensures each worker gets different exit IP
        max_rotation_attempts=10    # Try up to 10 times to get unique IP
    )

    # List of videos to process in parallel
    video_ids = [
        "dQw4w9WgXcQ",  # Rick Astley
        "kJQP7kiw5Fk",  # Luis Fonsi - Despacito
        "9bZkp7q19f0",  # PSY - Gangnam Style
    ]

    def process_video(worker_id: int, video_id: str):
        """Worker function that acquires a connection from pool."""
        try:
            # Acquire connection from pool (auto-releases on exit)
            with pool.acquire(worker_id=worker_id) as fetcher:
                logger.debug(f"Worker {worker_id}: Processing {video_id}")
                transcript = fetcher.fetch_with_fallback(video_id)

                if transcript:
                    return {
                        'worker_id': worker_id,
                        'video_id': video_id,
                        'success': True,
                        'length': transcript['length'],
                        'duration': transcript['duration']
                    }
                else:
                    return {
                        'worker_id': worker_id,
                        'video_id': video_id,
                        'success': False
                    }
        except Exception as e:
            return {
                'worker_id': worker_id,
                'video_id': video_id,
                'success': False,
                'error': str(e)
            }

    # Process videos in parallel using thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(process_video, i, vid)
            for i, vid in enumerate(video_ids)
        ]

        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Print results
    logger.info("\n=== Results ===")
    for result in results:
        if result['success']:
            logger.success(f"✓ Worker {result['worker_id']}: {result['video_id']} - "
                          f"{result['length']} chars, {result['duration']}")
        else:
            error = result.get('error', 'Unknown error')
            logger.error(f"✗ Worker {result['worker_id']}: {result['video_id']} - {error}")

    # Show pool statistics
    stats = pool.get_stats()
    logger.info(f"\n=== Pool Statistics ===")
    logger.info(f"Connections: {stats['in_use']}/{stats['pool_size']} in use "
                f"({stats['utilization']:.1%} utilization)")
    logger.info(f"Unique exit IPs: {stats['unique_exit_ips']}/{stats['in_use']}")
    logger.error(f"All unique: {'✓ YES' if stats['all_unique'] else '✗ NO'}")
    if stats['active_exit_ips']:
        logger.info(f"Active IPs: {', '.join(stats['active_exit_ips'])}")