export interface WikiLink {
  text: string;
  start: number;
  end: number;
}

/**
 * Extract wiki-style links from markdown content
 * Regex: /\[\[([^\]]+)\]\]/g
 * Example: [[Another Note]] -> { text: "Another Note", start: 0, end: 16 }
 */
export function extractWikiLinks(content: string): WikiLink[] {
  const wikiLinkRegex = /\[\[([^\]]+)\]\]/g;
  const links: WikiLink[] = [];
  let match;

  while ((match = wikiLinkRegex.exec(content)) !== null) {
    links.push({
      text: match[1],
      start: match.index,
      end: match.index + match[0].length,
    });
  }

  return links;
}

/**
 * Replace wiki-style links with clickable links
 * Converts [[Note Title]] to a link element
 */
export function processWikiLinks(
  content: string,
  onLinkClick: (title: string) => void
): string {
  const wikiLinkRegex = /\[\[([^\]]+)\]\]/g;

  return content.replace(wikiLinkRegex, (match, title) => {
    return `<a href="#" data-wiki-link="${title}" class="wiki-link text-blue-600 hover:text-blue-800 underline">${title}</a>`;
  });
}

/**
 * Extract frontmatter from markdown (if any)
 */
export function extractFrontmatter(content: string): {
  frontmatter: Record<string, any>;
  content: string;
} {
  const frontmatterRegex = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/;
  const match = content.match(frontmatterRegex);

  if (!match) {
    return { frontmatter: {}, content };
  }

  const [, frontmatterStr, bodyContent] = match;
  const frontmatter: Record<string, any> = {};

  // Simple YAML-like parsing (key: value)
  frontmatterStr.split('\n').forEach((line) => {
    const [key, ...valueParts] = line.split(':');
    if (key && valueParts.length > 0) {
      frontmatter[key.trim()] = valueParts.join(':').trim();
    }
  });

  return { frontmatter, content: bodyContent };
}

/**
 * Generate table of contents from markdown headers
 */
export function generateTOC(content: string): Array<{ level: number; text: string; id: string }> {
  const headerRegex = /^(#{1,6})\s+(.+)$/gm;
  const toc: Array<{ level: number; text: string; id: string }> = [];
  let match;

  while ((match = headerRegex.exec(content)) !== null) {
    const level = match[1].length;
    const text = match[2].trim();
    const id = text.toLowerCase().replace(/[^\w]+/g, '-');

    toc.push({ level, text, id });
  }

  return toc;
}

/**
 * Truncate markdown content to a specified length (for previews)
 */
export function truncateMarkdown(content: string, maxLength: number): string {
  // Remove markdown formatting for preview
  let plain = content
    .replace(/^#{1,6}\s+/gm, '') // Remove headers
    .replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold
    .replace(/\*([^*]+)\*/g, '$1') // Remove italic
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Remove links
    .replace(/```[\s\S]*?```/g, '') // Remove code blocks
    .replace(/`([^`]+)`/g, '$1') // Remove inline code
    .replace(/\[\[([^\]]+)\]\]/g, '$1') // Remove wiki links
    .trim();

  if (plain.length <= maxLength) {
    return plain;
  }

  return plain.substring(0, maxLength) + '...';
}
