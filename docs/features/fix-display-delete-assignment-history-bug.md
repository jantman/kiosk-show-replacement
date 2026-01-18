# Fix Display Delete with Assignment History Bug

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

When deleting a display through the admin interface, the delete API returns a 500 Internal Server Error with a SQLAlchemy ProgrammingError when the display has associated assignment history records.

## Problem

Integration test `test_delete_display_with_confirmation` in `tests/integration/test_display_management.py` fails because the DELETE `/api/v1/displays/{id}` endpoint returns HTTP 500.

### Evidence from Test Logs

```
DELETE /api/v1/displays/1 -> 500
[parameters: [(None, 1), (None, 2)]]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
```

The error code `gkpj` is SQLAlchemy's ProgrammingError.

### Root Cause Analysis

The `AssignmentHistory` model (`kiosk_show_replacement/models/__init__.py:604`) has a foreign key to the displays table:

```python
display_id = Column(Integer, ForeignKey("displays.id"), nullable=False)
```

This foreign key constraint does not have `ondelete="CASCADE"`, so when a display with assignment history is deleted, the database constraint fails.

Additionally, the delete display API endpoint (`kiosk_show_replacement/api/v1.py:797-820`) does not clean up assignment history records before deleting the display.

## Investigation Needed

1. Confirm the exact error by adding more detailed logging
2. Determine if the issue is:
   - Missing CASCADE DELETE on foreign key
   - Missing cleanup in the delete API
   - Database state inconsistency from previous tests

## Files Involved

### Backend
- `kiosk_show_replacement/models/__init__.py` - AssignmentHistory model (line 604-643)
- `kiosk_show_replacement/api/v1.py` - delete_display endpoint (lines 795-820)

## Proposed Solution

Option 1: Add CASCADE DELETE to the foreign key:
```python
display_id = Column(Integer, ForeignKey("displays.id", ondelete="CASCADE"), nullable=False)
```

Option 2: Delete assignment history in the delete_display API before deleting the display:
```python
# In delete_display function:
AssignmentHistory.query.filter_by(display_id=display_id).delete()
db.session.delete(display)
db.session.commit()
```

Option 3: Use soft delete instead of hard delete - set display as archived rather than deleting.

## Implementation Plan

### Investigation Results

The root cause has been confirmed:
1. `AssignmentHistory.display_id` (line 658 in models/__init__.py) uses `ForeignKey("displays.id")` without `ondelete="CASCADE"`
2. The `delete_display` function (lines 798-823 in api/v1.py) performs a hard delete without cleaning up related `AssignmentHistory` records
3. The initial migration (line 149) creates the foreign key without `ondelete` parameter
4. Slideshows use soft delete (setting `is_active=False`), which is why they don't have this problem

### Selected Approach: Option 1 - Database Migration with CASCADE DELETE

Option 1 is the preferred approach because:
- It enforces data integrity at the database level
- Ensures consistency regardless of how the display is deleted (API, direct DB access, etc.)
- Is the proper way to handle parent-child relationships with hard deletes

Since SQLite doesn't support `ALTER TABLE` for foreign key constraints, we'll use Alembic's `batch_alter_table` which recreates the table with the new constraint.

### Milestone 1: Add CASCADE DELETE Migration (FDD-1) ✅ COMPLETE

| Task | Description | Prefix | Status |
|------|-------------|--------|--------|
| 1.1  | Update `AssignmentHistory` model to add `ondelete="CASCADE"` to `display_id` foreign key | FDD-1.1 | ✅ |
| 1.2  | Create Alembic migration to alter the foreign key constraint using batch operations | FDD-1.2 | ✅ |
| 1.3  | Run migration and verify it works | FDD-1.3 | ✅ |
| 1.4  | Add unit test for deleting display with assignment history | FDD-1.4 | ✅ |

**Additional changes made during Milestone 1:**
- Added `passive_deletes=True` to the `AssignmentHistory.display` relationship to let the database handle cascade deletes
- Added SQLite foreign key enforcement via `PRAGMA foreign_keys=ON` event listener in `app.py`
- Fixed `test_display_lifecycle.py::test_archive_display_sets_correct_fields` to create a real slideshow (now required with foreign key enforcement)

### Milestone 2: Acceptance Criteria (FDD-2)

| Task | Description | Prefix |
|------|-------------|--------|
| 2.1  | Remove `@pytest.mark.xfail` from `test_delete_display_with_confirmation` | FDD-2.1 |
| 2.2  | Run all nox sessions and verify all tests pass | FDD-2.2 |
| 2.3  | Move feature document to `docs/features/completed/` | FDD-2.3 |

## Acceptance Criteria

1. Deleting a display through the admin interface succeeds
2. Assignment history is cascaded when display is deleted (database-level enforcement)
3. Integration test `test_delete_display_with_confirmation` passes (xfail marker removed)
4. All existing tests continue to pass
5. New unit test covers the fix
6. Database migration properly handles the foreign key constraint update
