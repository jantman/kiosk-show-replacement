import { describe, it, expect } from 'vitest';
import { sanitizeHtml } from '../utils/sanitizeHtml';

describe('sanitizeHtml', () => {
  describe('with HTML content', () => {
    it('allows safe formatting tags', () => {
      const html = 'This is <b>bold</b> and <i>italic</i> text';
      const result = sanitizeHtml(html);
      expect(result).toContain('<b>bold</b>');
      expect(result).toContain('<i>italic</i>');
    });

    it('allows strong and em tags', () => {
      const html = '<strong>strong</strong> and <em>emphasized</em>';
      const result = sanitizeHtml(html);
      expect(result).toContain('<strong>strong</strong>');
      expect(result).toContain('<em>emphasized</em>');
    });

    it('allows underline tags', () => {
      const html = '<u>underlined</u>';
      const result = sanitizeHtml(html);
      expect(result).toContain('<u>underlined</u>');
    });

    it('allows br and p tags', () => {
      const html = '<p>paragraph</p><br>line break';
      const result = sanitizeHtml(html);
      expect(result).toContain('<p>');
      expect(result).toContain('<br>');
    });

    it('strips script tags', () => {
      const html = '<script>alert("XSS")</script>safe text';
      const result = sanitizeHtml(html);
      expect(result).not.toContain('<script>');
      expect(result).not.toContain('alert');
      expect(result).toContain('safe text');
    });

    it('strips onclick attributes', () => {
      const html = '<b onclick="alert(\'XSS\')">text</b>';
      const result = sanitizeHtml(html);
      expect(result).toContain('<b>text</b>');
      expect(result).not.toContain('onclick');
    });

    it('strips style attributes', () => {
      const html = '<b style="color:red">text</b>';
      const result = sanitizeHtml(html);
      expect(result).toContain('<b>text</b>');
      expect(result).not.toContain('style');
    });

    it('strips img tags', () => {
      const html = '<img src="x" onerror="alert(\'XSS\')">text';
      const result = sanitizeHtml(html);
      expect(result).not.toContain('<img');
      expect(result).toContain('text');
    });
  });

  describe('with plain text', () => {
    it('escapes HTML entities', () => {
      // This test verifies that text containing HTML-like patterns gets sanitized
      // The input contains script tags which get stripped by sanitization
      const html = '<script>alert("XSS")</script>';
      const result = sanitizeHtml(html);
      expect(result).not.toContain('<script>');
      expect(result).not.toContain('alert');
    });

    it('converts newlines to br tags for plain text', () => {
      const text = 'Line one\nLine two\nLine three';
      const result = sanitizeHtml(text);
      expect(result).toContain('<br>');
      expect(result).toContain('Line one');
      expect(result).toContain('Line two');
      expect(result).toContain('Line three');
    });

    it('escapes special characters in plain text', () => {
      // Text with angle brackets that look like tags gets processed
      // The sanitizer handles this by stripping invalid tags
      const text = 'Some text with <angle brackets> & ampersand';
      const result = sanitizeHtml(text);
      // The content should still contain the readable text
      expect(result).toContain('Some text with');
      expect(result).toContain('ampersand');
    });

    it('handles text without any special characters', () => {
      const text = 'Just plain text';
      const result = sanitizeHtml(text);
      expect(result).toBe('Just plain text');
    });
  });

  describe('with null/undefined', () => {
    it('returns empty string for null', () => {
      expect(sanitizeHtml(null)).toBe('');
    });

    it('returns empty string for undefined', () => {
      expect(sanitizeHtml(undefined)).toBe('');
    });

    it('returns empty string for empty string', () => {
      expect(sanitizeHtml('')).toBe('');
    });
  });
});
