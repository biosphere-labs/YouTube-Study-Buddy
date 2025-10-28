/**
 * Extract YouTube video ID from various URL formats
 * Supports:
 * - https://www.youtube.com/watch?v=VIDEO_ID
 * - https://youtu.be/VIDEO_ID
 * - https://www.youtube.com/embed/VIDEO_ID
 */
export function extractVideoId(url: string): string | null {
  const patterns = [
    /youtube\.com\/watch\?v=([^&]+)/,
    /youtu\.be\/([^?]+)/,
    /youtube\.com\/embed\/([^?]+)/,
  ];

  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return null;
}

/**
 * Get YouTube thumbnail URL for a video
 * @param videoId YouTube video ID
 * @param quality 'default' | 'mqdefault' | 'hqdefault' | 'sddefault' | 'maxresdefault'
 */
export function getThumbnailUrl(
  videoId: string,
  quality: 'default' | 'mqdefault' | 'hqdefault' | 'sddefault' | 'maxresdefault' = 'hqdefault'
): string {
  return `https://img.youtube.com/vi/${videoId}/${quality}.jpg`;
}

/**
 * Get YouTube embed URL for a video
 */
export function getEmbedUrl(videoId: string): string {
  return `https://www.youtube.com/embed/${videoId}`;
}

/**
 * Validate if a string is a valid YouTube URL
 */
export function isValidYouTubeUrl(url: string): boolean {
  return extractVideoId(url) !== null;
}
