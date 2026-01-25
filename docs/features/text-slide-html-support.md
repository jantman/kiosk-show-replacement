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

## Implementation Plan

### Technical Approach

**Current State:**
- Display view (`kiosk_show_replacement/templates/display/slideshow.html`) renders text slides using `escapeHtml()` which converts all HTML entities to safe escaped text
- Line breaks are preserved via CSS `white-space: pre-wrap` on the `.text-content .content` element
- Admin preview (`frontend/src/pages/SlideshowDetail.tsx`) shows first 50 characters of text content as plain text

**Chosen Approach: Client-side HTML Sanitization with DOMPurify**

DOMPurify is a battle-tested, lightweight (~10KB minified) library specifically designed for XSS-safe HTML sanitization. Benefits:
- No backend changes needed - text is stored as-is, sanitized at render time
- Well-maintained and widely used (npm, CDN)
- Highly configurable whitelist of allowed tags and attributes
- Maintains backwards compatibility - plain text works identically

**Key Files to Modify:**
1. `kiosk_show_replacement/templates/display/slideshow.html` - Replace `escapeHtml()` with DOMPurify sanitization
2. `frontend/src/pages/SlideshowDetail.tsx` - Update admin preview to render safe HTML

### Milestones

#### Milestone 1: Display View HTML Support (M1)

**M1.1: Create failing regression tests**
- Add integration test for HTML rendering in text slides (`<b>`, `<i>`, `<u>`, `<strong>`, `<em>`)
- Add integration test for unsafe HTML stripping (`<script>`, `onclick`, etc.)
- Add integration test confirming plain text with line breaks still works

**M1.2: Add DOMPurify to display template**
- Include DOMPurify via CDN in slideshow.html
- Create `sanitizeHtml()` function that allows only whitelisted tags

**M1.3: Replace escapeHtml with sanitizeHtml**
- Update text slide rendering to use `sanitizeHtml()` instead of `escapeHtml()`
- Configure DOMPurify to allow: `<b>`, `<strong>`, `<i>`, `<em>`, `<u>`, `<br>`, `<p>`
- Ensure all attributes are stripped (no `style`, `onclick`, etc.)

**M1.4: Handle line breaks**
- For text without HTML tags, convert newlines to `<br>` before sanitization
- For text with HTML tags, trust user-provided `<br>` and `<p>` tags
- Verify existing line break behavior is preserved

#### Milestone 2: Admin Preview Support (M2)

**M2.1: Add tests for admin preview**
- Add integration test verifying HTML renders in admin slide preview

**M2.2: Add DOMPurify to React frontend**
- Install DOMPurify package (`npm install dompurify @types/dompurify`)
- Create reusable sanitization utility

**M2.3: Update admin preview component**
- Modify SlideshowDetail.tsx to safely render HTML in slide preview
- Use `dangerouslySetInnerHTML` with sanitized content

#### Milestone 3: Acceptance Criteria (M3)

**M3.1: Documentation**
- Update user documentation if applicable
- Update CLAUDE.md if needed

**M3.2: Verify tests pass**
- Run all unit tests
- Run all integration tests
- Run all e2e tests

**M3.3: Final verification**
- Run all nox sessions
- Manual verification of feature

**M3.4: Complete feature**
- Move feature file to `docs/features/completed/`

---

## Progress

- [x] M1: Display View HTML Support ✅ COMPLETE
  - [x] M1.1: Create failing regression tests
  - [x] M1.2: Add DOMPurify to display template (local file, not CDN)
  - [x] M1.3: Replace escapeHtml with sanitizeHtml
  - [x] M1.4: Handle line breaks (auto-convert \n to <br> for plain text)
- [x] M2: Admin Preview Support ✅ COMPLETE
  - [x] M2.1: Add tests for admin preview
  - [x] M2.2: Add DOMPurify to React frontend (npm install dompurify)
  - [x] M2.3: Update admin preview component (SlideshowDetail.tsx)
- [ ] M3: Acceptance Criteria
  - [ ] M3.1: Documentation
  - [ ] M3.2: Verify tests pass
  - [ ] M3.3: Final verification
  - [ ] M3.4: Complete feature

---

## Acceptance Criteria

- [ ] Basic HTML tags (`<b>`, `<i>`, `<u>`, `<br>`, `<p>`, `<strong>`, `<em>`) render correctly in text slides
- [ ] Text without HTML tags continues to work as before (line breaks preserved)
- [ ] Unsafe HTML tags and attributes are stripped/escaped
- [ ] Works in both admin preview and display view
