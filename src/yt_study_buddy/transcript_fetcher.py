"""
YouTube transcript fetcher with optional proxy support.

Fetches transcripts using youtube-transcript-api with optional proxy routing.
When tor-proxy-middleware is installed, uses it for resilient proxy handling.
Falls back to yt-dlp if proxy fetch fails.
"""
import random
import re
import socket
import time
from typing import Optional, List, Dict, Any

from loguru import logger
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

from .ytdlp_fallback import YtDlpFallback

# Optional: tor-proxy-middleware for resilient proxy handling
try:
    from tor_proxy_middleware import RotatingTorClient, RetryConfig
    PROXY_MIDDLEWARE_AVAILABLE = True
except ImportError:
    RotatingTorClient = None
    RetryConfig = None
    PROXY_MIDDLEWARE_AVAILABLE = False


class TranscriptFetcher:
    """
    Fetch YouTube transcripts with optional proxy support.

    When tor-proxy-middleware is installed and a proxy client is provided,
    uses it for resilient proxy handling with automatic retries.
    Otherwise, fetches directly or through a simple proxy URL.
    """

    def __init__(
        self,
        proxy_client: Optional["RotatingTorClient"] = None,
        proxy_url: Optional[str] = None,
    ):
        """
        Initialize transcript fetcher.

        Args:
            proxy_client: Optional RotatingTorClient for resilient proxy handling
            proxy_url: Optional simple proxy URL (e.g., "socks5://127.0.0.1:9050")
                       Only used if proxy_client is not provided
        """
        self.proxy_client = proxy_client
        self.proxy_url = proxy_url
        self.ytdlp_fallback = YtDlpFallback()

        # Determine proxy configuration
        if self.proxy_client:
            # Use proxy URL from client
            self._proxy_config = GenericProxyConfig(
                http_url=self.proxy_client.tor_config.socks_url,
                https_url=self.proxy_client.tor_config.socks_url
            )
            logger.info("TranscriptFetcher initialized with proxy middleware client")
        elif self.proxy_url:
            # Use simple proxy URL
            self._proxy_config = GenericProxyConfig(
                http_url=self.proxy_url,
                https_url=self.proxy_url
            )
            logger.info(f"TranscriptFetcher initialized with proxy: {self.proxy_url}")
        else:
            # No proxy - direct connection
            self._proxy_config = None
            logger.info("TranscriptFetcher initialized without proxy (direct connection)")

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
            available_langs = [t.language_code for t in transcript_list]

            if available_langs:
                return False, f"No transcript in {languages}, available: {available_langs[:5]}"
            else:
                return False, "No transcripts available for this video"

        except Exception as e:
            # If check fails, allow attempt (might still work)
            return True, None

    def _fetch_transcript_once(
        self,
        video_id: str,
        languages: List[str],
        timeout: float
    ) -> Optional[Dict[str, Any]]:
        """
        Single attempt to fetch transcript.

        Args:
            video_id: YouTube video ID
            languages: List of language codes
            timeout: Timeout in seconds

        Returns:
            Transcript data dict or None if failed
        """
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)

        try:
            # Create API with or without proxy
            if self._proxy_config:
                api = YouTubeTranscriptApi(proxy_config=self._proxy_config)
            else:
                api = YouTubeTranscriptApi()

            fetched = api.fetch(video_id, languages=languages)
            transcript_list = list(fetched)

            # Process transcript
            transcript_text = ' '.join([snippet.text for snippet in transcript_list])
            transcript_text = re.sub(r'\s+', ' ', transcript_text)
            transcript_text = transcript_text.replace('[Music]', '').replace('[Applause]', '')

            # Calculate duration
            duration_info = None
            if transcript_list:
                last_snippet = transcript_list[-1]
                duration_seconds = last_snippet.start + last_snippet.duration
                duration_minutes = int(duration_seconds / 60)
                duration_info = f"~{duration_minutes} minutes"

            return {
                'transcript': transcript_text,
                'duration': duration_info,
                'length': len(transcript_text),
                'segments': transcript_list,
                'method': 'proxy' if self._proxy_config else 'direct'
            }

        except Exception as e:
            logger.debug(f"Transcript fetch failed: {e}")
            return None

        finally:
            socket.setdefaulttimeout(old_timeout)

    def fetch_transcript(
        self,
        video_id: str,
        languages: List[str] = ['en'],
        max_retries: int = 5,
        base_timeout: float = 60.0,
        max_timeout: float = 120.0,
        check_availability: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch transcript with retries and optional proxy rotation.

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
        # Quick availability check
        if check_availability:
            is_available, error_msg = self.check_transcript_availability(video_id, languages)
            if not is_available:
                logger.error(f"Transcript not available: {error_msg}")
                return None

        for attempt in range(max_retries):
            attempt_num = attempt + 1

            # Handle retries with rotation if proxy client available
            if attempt > 0:
                logger.info(f"Retry attempt {attempt_num}/{max_retries}...")

                if self.proxy_client:
                    # Use middleware for rotation
                    try:
                        self.proxy_client.force_rotation()
                    except Exception as e:
                        logger.warning(f"Circuit rotation failed: {e}")
                        # Add extra delay if rotation failed
                        extra_delay = 10 * attempt
                        logger.info(f"Adding {extra_delay}s delay...")
                        time.sleep(extra_delay)

                # Exponential backoff with jitter
                backoff = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Waiting {backoff:.1f}s before retry...")
                time.sleep(backoff)

            # Add small random delay to appear human-like
            time.sleep(random.uniform(0.5, 2))

            # Calculate adaptive timeout
            timeout = min(base_timeout * (1.5 ** attempt), max_timeout)
            logger.debug(f"Attempt {attempt_num} with timeout {timeout:.0f}s")

            # Try to fetch
            result = self._fetch_transcript_once(video_id, languages, timeout)

            if result:
                logger.success(f"Successfully fetched transcript on attempt {attempt_num}")

                # Record success if using proxy client
                if self.proxy_client:
                    self.proxy_client.record_success(video_id=video_id, attempt=attempt_num)

                return result
            else:
                # Record failure if using proxy client
                if self.proxy_client:
                    self.proxy_client.record_failure(video_id=video_id, attempt=attempt_num)

        logger.error(f"All {max_retries} attempts failed")
        return None

    def fetch_with_fallback(
        self,
        video_id: str,
        languages: List[str] = ['en']
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch transcript via proxy first, fall back to yt-dlp if that fails.

        Args:
            video_id: YouTube video ID
            languages: List of language codes

        Returns:
            Dictionary with transcript data or None if all methods failed
        """
        # Try proxy first (if configured)
        if self._proxy_config:
            logger.info("Fetching transcript via proxy...")
            result = self.fetch_transcript(video_id, languages)

            if result:
                logger.success("Successfully fetched via proxy")
                return result
            else:
                logger.warning("Proxy fetch failed")

        # Fall back to yt-dlp
        logger.info("Attempting yt-dlp fallback...")
        ytdlp_result = self.ytdlp_fallback.fetch_transcript(video_id, languages)

        if ytdlp_result:
            logger.success("Successfully fetched via yt-dlp fallback")
            ytdlp_result['method'] = 'yt-dlp'
            return ytdlp_result
        else:
            logger.error("yt-dlp fallback also failed")
            return None

    def get_video_title(
        self,
        video_id: str,
        max_retries: int = 3,
        timeout: int = 30,
        worker_id: Optional[int] = None
    ) -> str:
        """
        Get video title using YouTube oEmbed API.

        Uses proxy client's request_with_retry if available.

        Args:
            video_id: YouTube video ID
            max_retries: Maximum retry attempts
            timeout: Timeout per attempt in seconds
            worker_id: Optional worker ID for logging

        Returns:
            Video title or fallback "Video_{video_id}"
        """
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        fallback = f"Video_{video_id}"

        if self.proxy_client:
            # Use middleware's retry logic
            response = self.proxy_client.get_with_retry(
                url,
                request_id=f"title_{video_id}",
                retry_config=RetryConfig(
                    max_retries=max_retries,
                    base_timeout=timeout,
                    max_timeout=timeout * 2
                ) if RetryConfig else None
            )

            if response and response.status_code == 200:
                try:
                    title = response.json().get('title')
                    if title:
                        # Clean title for filename
                        clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
                        return clean_title[:100]
                except Exception as e:
                    logger.warning(f"Failed to parse title response: {e}")

        else:
            # Direct request without middleware
            import requests
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, timeout=timeout)
                    if response.status_code == 200:
                        title = response.json().get('title')
                        if title:
                            clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                            clean_title = re.sub(r'\s+', ' ', clean_title).strip()
                            return clean_title[:100]
                except Exception as e:
                    logger.debug(f"Title fetch attempt {attempt + 1} failed: {e}")
                    time.sleep(2 ** attempt)

        logger.warning(f"Could not fetch title, using fallback: {fallback}")
        return fallback


def create_transcript_fetcher(
    use_proxy: bool = True,
    proxy_host: str = '127.0.0.1',
    proxy_port: int = 9050,
    **kwargs
) -> TranscriptFetcher:
    """
    Factory function to create a TranscriptFetcher.

    Args:
        use_proxy: Whether to use proxy (default: True)
        proxy_host: Proxy host (default: 127.0.0.1)
        proxy_port: Proxy SOCKS port (default: 9050)
        **kwargs: Additional arguments passed to RotatingTorClient if available

    Returns:
        Configured TranscriptFetcher instance
    """
    if not use_proxy:
        return TranscriptFetcher()

    if PROXY_MIDDLEWARE_AVAILABLE:
        # Use the full middleware client
        from tor_proxy_middleware import TorConfig
        client = RotatingTorClient(
            tor_config=TorConfig(host=proxy_host, socks_port=proxy_port),
            **kwargs
        )
        return TranscriptFetcher(proxy_client=client)
    else:
        # Use simple proxy URL
        proxy_url = f"socks5://{proxy_host}:{proxy_port}"
        return TranscriptFetcher(proxy_url=proxy_url)
