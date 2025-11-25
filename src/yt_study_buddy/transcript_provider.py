"""
Transcript provider interface and implementations.

Supports both proxy and direct connections:
- Proxy (default): Recommended for high-volume use, bypasses IP blocks
- Direct connection: For low-volume use (<50 videos/day from residential IPs)
"""
import random
import re
import time
from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any, Optional

from loguru import logger

from .transcript_fetcher import create_transcript_fetcher


class TranscriptProvider(Protocol):
    """
    Protocol (structural typing) - like TypeScript interfaces.
    Any class that implements these methods automatically satisfies this interface.
    No inheritance required!
    """

    def get_transcript(self, video_id: str) -> Dict[str, Any]:
        """Get transcript data for a video ID."""
        ...

    def get_video_title(self, video_id: str) -> str:
        """Get video title for a video ID."""
        ...


class AbstractTranscriptProvider(ABC):
    """
    Abstract Base Class (inheritance-based) - traditional OOP approach.
    Subclasses MUST implement abstract methods.
    """

    @abstractmethod
    def get_transcript(self, video_id: str) -> Dict[str, Any]:
        """Get transcript data for a video ID."""
        pass

    @abstractmethod
    def get_video_title(self, video_id: str) -> str:
        """Get video title for a video ID."""
        pass

    def get_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL - common implementation."""
        patterns = [
            r'(?:v=|/v/|youtu\.be/|/embed/|/watch\?.*v=)([^&\n?#]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None


class ProxyTranscriptProvider(AbstractTranscriptProvider):
    """
    Proxy-based transcript provider - bypasses IP blocks via SOCKS proxy.

    When tor-proxy-middleware is installed, provides resilient proxy handling
    with automatic circuit rotation. Otherwise uses a simple proxy URL.
    """

    def __init__(self, proxy_host: str = '127.0.0.1', proxy_port: int = 9050):
        """
        Initialize proxy-based transcript provider with yt-dlp fallback.

        Args:
            proxy_host: SOCKS proxy host (default: 127.0.0.1)
            proxy_port: SOCKS proxy port (default: 9050)
        """
        self.fetcher = create_transcript_fetcher(
            use_proxy=True,
            proxy_host=proxy_host,
            proxy_port=proxy_port
        )
        self._proxy_verified = False
        self.stats = {
            'proxy_success': 0,
            'proxy_failure': 0,
            'ytdlp_success': 0,
            'ytdlp_failure': 0,
            'total_attempts': 0
        }

    def verify_proxy_connection(self) -> bool:
        """
        Check if proxy connection is working.

        Returns:
            True if proxy is working, False otherwise
        """
        if not self._proxy_verified:
            logger.info("Verifying proxy connection...")
            try:
                # Try to get exit IP through proxy
                if self.fetcher.proxy_client:
                    self.fetcher.proxy_client._get_exit_ip()
                    self._proxy_verified = True
                    logger.success("Proxy connection verified")
                elif self.fetcher.proxy_url:
                    # Simple check with proxy URL
                    import requests
                    proxies = {'http': self.fetcher.proxy_url, 'https': self.fetcher.proxy_url}
                    response = requests.get('https://api.ipify.org', proxies=proxies, timeout=10)
                    self._proxy_verified = response.status_code == 200
                    if self._proxy_verified:
                        logger.success(f"Proxy connection verified (exit IP: {response.text})")
                else:
                    logger.warning("No proxy configured")
                    self._proxy_verified = False
            except Exception as e:
                logger.error(f"Proxy connection not available: {e}")
                self._proxy_verified = False

        return self._proxy_verified

    def get_transcript(self, video_id: str) -> Dict[str, Any]:
        """
        Get transcript with statistics tracking.

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary with transcript data

        Raises:
            Exception: If both proxy and yt-dlp fallback fail
        """
        self.stats['total_attempts'] += 1

        try:
            # Add small random delay to avoid appearing automated
            time.sleep(random.uniform(0.5, 1.5))

            # Fetch transcript via proxy with yt-dlp fallback
            result = self.fetcher.fetch_with_fallback(
                video_id=video_id,
                languages=['en']
            )

            if result:
                # Check which method was used
                if result.get('method') == 'yt-dlp':
                    self.stats['ytdlp_success'] += 1
                else:
                    self.stats['proxy_success'] += 1
                return result
            else:
                self.stats['proxy_failure'] += 1
                self.stats['ytdlp_failure'] += 1
                raise Exception("Both proxy and yt-dlp fallback failed")

        except Exception as e:
            # Check if it's a rate limiting error and retry
            if "429" in str(e) or "Too Many Requests" in str(e):
                logger.warning(f"Rate limited, attempting retry with backoff...")
                return self._retry_with_backoff(video_id, max_retries=3)
            else:
                raise Exception(f"Could not get transcript: {e}")

    def get_video_title(self, video_id: str) -> str:
        """
        Get video title using proxy.

        Args:
            video_id: YouTube video ID

        Returns:
            Video title cleaned for filename use
        """
        try:
            title = self.fetcher.get_video_title(video_id)
            if title and not title.startswith("Video_"):
                return title

        except Exception as e:
            logger.error(f"Warning: Could not fetch video title via proxy: {e}")

        return f"Video_{video_id}"

    def _retry_with_backoff(self, video_id: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Retry transcript fetching with exponential backoff.

        Args:
            video_id: YouTube video ID
            max_retries: Maximum number of retry attempts

        Returns:
            Dictionary with transcript data

        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(max_retries):
            try:
                wait_time = 5 * (2 ** attempt)
                logger.warning(f"Retry {attempt + 1}/{max_retries} - waiting {wait_time} seconds...")
                time.sleep(wait_time)
                time.sleep(random.uniform(1, 3))

                result = self.fetcher.fetch_with_fallback(
                    video_id=video_id,
                    languages=['en']
                )

                if result:
                    logger.success(f"Retry successful!")
                    return result
                else:
                    raise Exception("Fetch returned None")

            except Exception as retry_e:
                if attempt == max_retries - 1:
                    raise Exception(f"All retry attempts failed. Last error: {retry_e}")
                else:
                    logger.error(f"Retry {attempt + 1} failed: {retry_e}")

        raise Exception("All retry attempts exhausted")

    def print_stats(self):
        """Print success rate statistics."""
        total = self.stats['total_attempts']
        if total == 0:
            logger.debug("No attempts yet")
            return

        logger.info("\n" + "="*50)
        logger.info("TRANSCRIPT FETCHING STATISTICS")
        logger.info("="*50)
        logger.debug(f"Total attempts: {total}")
        logger.success(f"Proxy successes: {self.stats['proxy_success']} ({self.stats['proxy_success']/total*100:.1f}%)")
        logger.success(f"YT-DLP successes: {self.stats['ytdlp_success']} ({self.stats['ytdlp_success']/total*100:.1f}%)")
        logger.error(f"Total failures: {self.stats['proxy_failure']} ({self.stats['proxy_failure']/total*100:.1f}%)")
        logger.info("="*50)


class DirectTranscriptProvider(AbstractTranscriptProvider):
    """
    Direct transcript provider - fetches transcripts without proxy.

    Use cases:
    - Low-volume personal use (<50 videos/day from residential IPs)
    - Development/testing
    - Faster processing when rate limits aren't a concern

    Warning: May encounter rate limiting with high volume or from cloud IPs.
    """

    def __init__(self):
        """Initialize direct transcript provider."""
        self.fetcher = create_transcript_fetcher(use_proxy=False)
        self.stats = {
            'direct_success': 0,
            'direct_failure': 0,
            'total_attempts': 0
        }

    def get_transcript(self, video_id: str) -> Dict[str, Any]:
        """
        Fetch transcript directly using youtube_transcript_api.

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary with transcript data

        Raises:
            Exception: If transcript fetch fails
        """
        self.stats['total_attempts'] += 1

        try:
            # Add small random delay to avoid appearing automated
            time.sleep(random.uniform(0.5, 1.5))

            # Fetch transcript directly
            result = self.fetcher.fetch_transcript(video_id=video_id, languages=['en'])

            if result:
                self.stats['direct_success'] += 1
                return result
            else:
                self.stats['direct_failure'] += 1
                raise Exception("Direct fetch returned None")

        except Exception as e:
            self.stats['direct_failure'] += 1

            # Provide helpful error messages for common issues
            error_msg = str(e).lower()
            if "429" in error_msg or "too many requests" in error_msg or "rate limit" in error_msg:
                raise Exception(
                    f"Rate limit exceeded. YouTube is temporarily blocking your IP.\n"
                    f"Solutions:\n"
                    f"  1. Wait 15-30 minutes before retrying\n"
                    f"  2. Remove --no-proxy flag to use proxy\n"
                    f"  3. Process fewer videos at once\n"
                    f"Original error: {e}"
                )
            elif "transcripts are disabled" in error_msg or "no transcript" in error_msg:
                raise Exception(
                    f"This video does not have transcripts available.\n"
                    f"Original error: {e}"
                )
            else:
                raise Exception(f"Failed to fetch transcript: {e}")

    def get_video_title(self, video_id: str) -> str:
        """
        Get video title using direct connection.

        Args:
            video_id: YouTube video ID

        Returns:
            Video title cleaned for filename use
        """
        return self.fetcher.get_video_title(video_id)

    def print_stats(self):
        """Print success rate statistics."""
        total = self.stats['total_attempts']
        if total == 0:
            logger.debug("No attempts yet")
            return

        logger.info("\n" + "="*50)
        logger.info("TRANSCRIPT FETCHING STATISTICS (DIRECT)")
        logger.info("="*50)
        logger.debug(f"Total attempts: {total}")
        logger.success(f"Direct successes: {self.stats['direct_success']} ({self.stats['direct_success']/total*100:.1f}%)")
        logger.error(f"Direct failures: {self.stats['direct_failure']} ({self.stats['direct_failure']/total*100:.1f}%)")
        logger.info("="*50)


# Factory function for creating providers
def create_transcript_provider(provider_type: str = "proxy", **kwargs) -> TranscriptProvider:
    """
    Factory function that returns a TranscriptProvider.

    Args:
        provider_type: Type of provider ('proxy' or 'direct')
            - 'proxy' (default): Uses SOCKS proxy, recommended for high-volume use
            - 'direct': Direct connection, for low-volume use (<50 videos/day)
        **kwargs: Additional arguments passed to provider constructor
            For 'proxy':
                - proxy_host: Proxy host (default: '127.0.0.1')
                - proxy_port: Proxy port (default: 9050)
            For 'direct': no additional arguments

    Returns:
        TranscriptProvider instance (ProxyTranscriptProvider or DirectTranscriptProvider)
    """
    if provider_type == "proxy":
        return ProxyTranscriptProvider(**kwargs)
    elif provider_type == "direct":
        return DirectTranscriptProvider()
    else:
        raise ValueError(f"Unknown provider type: {provider_type}. Valid options: 'proxy', 'direct'")


# Type checking example
def process_with_provider(provider: TranscriptProvider, video_id: str) -> None:
    """
    This function accepts ANY object that implements the TranscriptProvider protocol.
    No inheritance required - just the right methods (duck typing + type hints).
    """
    transcript_data = provider.get_transcript(video_id)
    title = provider.get_video_title(video_id)
    logger.info(f"Processed '{title}': {transcript_data['length']} characters")
