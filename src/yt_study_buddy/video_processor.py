"""
Video processing utilities for YouTube transcript and metadata extraction.
Supports both Tor proxy and direct connections based on user preference.
"""
import re
from typing import Optional

from .transcript_provider import TranscriptProvider, create_transcript_provider
from loguru import logger


class VideoProcessor:
    """Handles YouTube video processing using Tor-based transcript provider."""

    def __init__(self, provider_type: str = "tor", **provider_kwargs):
        """
        Initialize with specified transcript provider.

        Args:
            provider_type: "tor" (default) or "direct"
                - "tor": Uses Tor proxy, recommended for high-volume use
                - "direct": Direct connection, for low-volume use (<50 videos/day)
            **provider_kwargs: Additional arguments passed to provider (e.g., tor_host, tor_port)
        """
        self.provider: TranscriptProvider = create_transcript_provider(provider_type, **provider_kwargs)
        self.provider_type = provider_type

    def get_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from any YouTube URL format."""
        patterns = [
            r'(?:v=|/v/|youtu\.be/|/embed/|/watch\?.*v=)([^&\n?#]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_video_title(self, video_id: str, worker_id=None) -> str:
        """Get video title using the configured provider.

        Args:
            video_id: YouTube video ID
            worker_id: Optional worker ID for logging/debugging (not used by provider)
        """
        return self.provider.get_video_title(video_id)

    def get_transcript(self, video_id: str) -> dict:
        """Get transcript using configured provider (Tor or direct)."""
        try:
            if self.provider_type == "tor":
                logger.info(f"  Using Tor provider...")
            else:
                logger.info(f"  Using direct connection...")
            return self.provider.get_transcript(video_id)
        except Exception as e:
            if self.provider_type == "tor":
                logger.error(f"  Tor provider failed: {e}")
                logger.info("  Make sure Tor proxy is running (docker-compose up -d tor-proxy)")
            else:
                logger.error(f"  Direct connection failed: {e}")
            raise

    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename for cross-platform compatibility."""
        # Remove/replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', ' ', filename).strip()
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        return filename or "unnamed_video"