import DOMPurify from 'dompurify';

/**
 * Allowed HTML tags for text slide formatting.
 * Only basic text formatting tags are allowed to prevent XSS attacks.
 */
const ALLOWED_TAGS = ['b', 'strong', 'i', 'em', 'u', 'br', 'p'];

/**
 * Sanitize HTML content allowing only safe formatting tags.
 * Uses DOMPurify to prevent XSS attacks while allowing basic text formatting.
 *
 * For plain text without HTML tags, newlines are converted to <br> tags.
 *
 * @param text - The text content, possibly containing HTML
 * @returns Sanitized HTML safe for rendering
 */
export function sanitizeHtml(text: string | null | undefined): string {
  if (!text) return '';

  // Check if text contains any HTML tags
  const hasHtmlTags = /<[^>]+>/.test(text);

  if (!hasHtmlTags) {
    // Plain text: escape HTML entities and convert newlines to <br>
    const escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
    return escaped.replace(/\n/g, '<br>');
  }

  // Text contains HTML: sanitize with DOMPurify
  // Only allow safe formatting tags, strip all attributes
  return DOMPurify.sanitize(text, {
    ALLOWED_TAGS,
    ALLOWED_ATTR: [], // No attributes allowed
  });
}
