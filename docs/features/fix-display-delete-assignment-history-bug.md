# Fix Display Delete with Assignment History Bug

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

## Acceptance Criteria

1. Deleting a display through the admin interface succeeds
2. Assignment history is either cascaded or cleaned up appropriately
3. Integration test `test_delete_display_with_confirmation` passes
4. All existing tests continue to pass
