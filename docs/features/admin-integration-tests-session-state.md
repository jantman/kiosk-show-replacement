# Admin Integration Tests - Session State

**Last Updated:** 2026-01-17
**Purpose:** Resume implementation in a new Claude Code session

## Current Progress

### Milestone Status

| Milestone | Status | Notes |
|-----------|--------|-------|
| M1: Test Infrastructure | **COMPLETE** | Committed in 5d71c92 |
| M2: Slideshow Management | **COMPLETE** | Committed in f5dc675, 7 tests passing |
| M3: Slideshow Items | Not started | |
| M4: Display Management | Not started | |
| M5: Display Detail | Not started | |
| M6: Dashboard | Not started | |
| M7: System Monitoring | Not started | |
| M8: Acceptance Criteria | Not started | |

## Next Steps

1. **Implement M3: Slideshow Items** - Test adding, editing, deleting, and reordering slideshow items

## M3: Slideshow Items - Tasks

From the implementation plan:

1. **AIT-3.1** Create `tests/integration/test_slideshow_items.py`
2. **AIT-3.2** Implement test: add image item via file upload
3. **AIT-3.3** Implement test: add image item via URL
4. **AIT-3.4** Implement test: add video item via file upload
5. **AIT-3.5** Implement test: add video item via URL
6. **AIT-3.6** Implement test: add URL item
7. **AIT-3.7** Implement test: add text item
8. **AIT-3.8** Implement test: edit existing item
9. **AIT-3.9** Implement test: delete item with confirmation
10. **AIT-3.10** Implement test: reorder items (move up/down)
11. **AIT-3.11** Run full test suite, ensure all tests pass

### Test Assets Available

Located in `tests/assets/`:
- **Images:** `smallPhoto.jpg`, `bigPhoto.jpg`, `tallPhoto.jpg`, `widePhoto.jpg`
- **Video:** `crash_into_pole.mpeg`

For URL-type slideshow items, use `https://example.com` (IANA reserved domain).

## Key Technical Patterns (from M2)

1. **SSE timeout issue**: Use `wait_for_load_state("domcontentloaded")` instead of `"load"` or `"networkidle"` because SSE connections keep the network active indefinitely.

2. **API response format**: API wraps responses in success envelope:
   ```python
   response_data = response.json().get("data", response.json())
   ```

3. **URL pattern matching**: Use regex with `expect(page).to_have_url()` for more reliable matching:
   ```python
   expect(page).to_have_url(re.compile(r".*/admin/slideshows/\d+$"), timeout=10000)
   ```

4. **Locator specificity**: Use specific selectors to avoid strict mode violations:
   ```python
   row.locator(".badge:has-text('Default')")  # Not just "text=Default"
   ```

## User Preferences (from conversation)

1. Use `poetry run nox` not `eval $(poetry env activate) && nox`
2. Tee test output to scratchpad file instead of piping through head/tail/grep
3. Continue between milestones without asking, as long as changes are committed
4. Test assets are in `tests/assets/` (4 photos, 1 video)
5. Use example.com for stable URLs in tests

## Commands Reference

```bash
# Run integration tests
poetry run nox -s test-integration

# Run format before lint
poetry run nox -s format

# Run lint
poetry run nox -s lint

# Scratchpad directory for output
/tmp/claude/-home-jantman-GIT-kiosk-show-replacement/<session-id>/scratchpad/
```

## Files Reference

### Key Test Files
- `tests/integration/conftest.py` - Shared fixtures
- `tests/integration/helpers.py` - Utility functions
- `tests/integration/test_slideshow_management.py` - M2 slideshow CRUD tests

### Documentation
- `docs/features/admin-integration-tests.md` - Full implementation plan
- `docs/features/fix-protected-route-redirect.md` - Bug discovered during M1
