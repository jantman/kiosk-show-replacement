# Basic HTML Support in Text Slides

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Allow basic HTML markup in text-type slides for simple formatting like bold, italic, and underline. Currently, HTML tags are displayed literally rather than being rendered.

## Observed Behavior

- **Slide content**: `Hello2s <b>Edited!</b>`
- **Expected display**: Hello2s **Edited!**
- **Actual display**: `Hello2s <b>Edited!</b>` (literal text, tags not rendered)

## Desired Behavior

- Support a limited set of safe HTML tags for text formatting in text slides
- If text content contains no HTML tags, preserve existing behavior (line breaks converted to `<br>`)
- If text content contains HTML tags, render the allowed tags

## Allowed HTML Tags

Suggested safe tags to support:
- `<b>`, `<strong>` - Bold
- `<i>`, `<em>` - Italic
- `<u>` - Underline
- `<br>` - Line break
- `<p>` - Paragraph

## Security Considerations

- Must sanitize HTML to prevent XSS attacks
- Only allow whitelisted tags
- Strip any attributes from tags (no `onclick`, `style`, etc.) or allow only safe attributes
- Consider using a sanitization library (e.g., DOMPurify on frontend, bleach on backend)

## Acceptance Criteria

- [ ] Basic HTML tags (`<b>`, `<i>`, `<u>`, `<br>`, `<p>`, `<strong>`, `<em>`) render correctly in text slides
- [ ] Text without HTML tags continues to work as before (line breaks preserved)
- [ ] Unsafe HTML tags and attributes are stripped/escaped
- [ ] Works in both admin preview and display view
