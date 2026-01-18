# Resolve All Mypy Type Errors

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

The `nox -s type_check` session currently fails with 110 mypy errors across 15 source files. The CLAUDE.md mentions an acceptable baseline of 11 errors (due to missing SQLAlchemy/Flask-Migrate stubs), but the error count has grown significantly.

This feature involves:
- Analyzing all current mypy errors
- Adding proper type annotations where missing
- Fixing type mismatches and incompatible assignments
- Adding appropriate type stubs or `# type: ignore` comments only where truly necessary (e.g., library issues)
- Reducing the error count to the acceptable baseline or ideally zero
- Updating CLAUDE.md if the acceptable baseline changes

---

## Implementation Plan

### Error Analysis Summary

Current state: **110 mypy errors across 15 files**

#### Error Categories

| Category | Count | Description |
|----------|-------|-------------|
| Column[T] vs T type mismatches | ~50 | SQLAlchemy Column types used where Python native types expected |
| Missing return type annotations | ~15 | Functions without return type annotations |
| Missing argument type annotations | ~8 | Functions with untyped parameters |
| Returning Any from function | ~15 | Query results returning Any instead of typed values |
| Incompatible return value type | ~10 | Return type mismatches (e.g., `tuple[Response, int]` vs `Response`) |
| Other (operator, attr-defined, etc.) | ~12 | Miscellaneous typing issues |

#### Files Affected (by error count)

1. `models/__init__.py` - ~35 errors (SQLAlchemy Column types)
2. `api/v1.py` - ~28 errors (Column types, missing annotations)
3. `display/views.py` - ~14 errors (Column types, return types)
4. `storage.py` - 12 errors (missing annotations, typing issues)
5. `auth/views.py` - 6 errors (return types, Column types)
6. `database_utils.py` - 6 errors (returning Any)
7. `sse.py` - 3 errors (missing annotations)
8. `migration_utils.py` - 3 errors (function return issues)
9. `storage_resilience.py` - 3 errors (missing annotations)
10. `api/__init__.py` - 2 errors (missing return types)
11. `logging_config.py` - 1 error (missing return type)
12. `metrics.py` - 1 error (missing return type)
13. `app.py` - 1 error (missing return type)

### Approach

The project uses SQLAlchemy 2.0 but defines models with the legacy `Column()` style. The cleanest fix is to:

1. **Enable the SQLAlchemy mypy plugin** - This helps mypy understand SQLAlchemy patterns
2. **Migrate model definitions to SQLAlchemy 2.0 `Mapped` style** - This provides proper typing for model attributes
3. **Add missing function type annotations** - Complete all function signatures
4. **Use explicit type annotations or casts where necessary** - For dynamic query results
5. **Add `# type: ignore` comments only for truly unavoidable library issues**

---

## Milestones

### Milestone 1: Configure SQLAlchemy Mypy Plugin

**Prefix: RME-1**

Configure the SQLAlchemy mypy plugin to improve type inference for SQLAlchemy models.

#### Tasks

1.1. Add `sqlalchemy[mypy]` to dev dependencies in pyproject.toml
1.2. Configure mypy to use the sqlalchemy plugin in pyproject.toml
1.3. Run type check to verify configuration and assess impact on error count
1.4. Commit configuration changes

### Milestone 2: Migrate Models to SQLAlchemy 2.0 Mapped Types

**Prefix: RME-2**

Update all model definitions in `models/__init__.py` to use SQLAlchemy 2.0 `Mapped[T]` type annotations, which provide proper type information to mypy.

#### Tasks

2.1. Update User model to use `Mapped[T]` for all columns
2.2. Update Display model to use `Mapped[T]` for all columns
2.3. Update Slideshow model to use `Mapped[T]` for all columns
2.4. Update SlideshowItem model to use `Mapped[T]` for all columns
2.5. Update AssignmentHistory model to use `Mapped[T]` for all columns
2.6. Update DisplayConfigurationTemplate model to use `Mapped[T]` for all columns
2.7. Run type check and verify model errors are resolved
2.8. Run all tests to ensure models still function correctly
2.9. Commit model changes

### Milestone 3: Fix Function Type Annotations

**Prefix: RME-3**

Add missing return type and parameter type annotations to all functions.

#### Tasks

3.1. Fix storage.py - add missing type annotations (2 functions)
3.2. Fix logging_config.py - add return type annotation
3.3. Fix metrics.py - add return type annotation
3.4. Fix app.py - add return type annotation
3.5. Fix api/__init__.py - add return type annotations (2 functions)
3.6. Fix sse.py - add missing type annotations
3.7. Fix storage_resilience.py - add missing type annotations (3 functions)
3.8. Run type check to verify progress
3.9. Commit annotation changes

### Milestone 4: Fix Type Mismatches in Views and API

**Prefix: RME-4**

Fix remaining type mismatches in view and API functions, including return types and query result typing.

#### Tasks

4.1. Fix auth/views.py - Column type assignments, return type issues
4.2. Fix database_utils.py - add proper return type annotations for query functions
4.3. Fix display/views.py - Column type assignments, return types, conditional function signatures
4.4. Fix api/v1.py - Column type issues, function parameter defaults, return types
4.5. Fix migration_utils.py - function return value issues
4.6. Run type check to verify all errors resolved
4.7. Run all tests to ensure functionality preserved
4.8. Commit view/API fixes

### Milestone 5: Acceptance Criteria

**Prefix: RME-5**

Final verification and documentation updates.

#### Tasks

5.1. Run full `poetry run nox -s type_check` and verify zero errors (or document remaining unavoidable errors)
5.2. Run all nox test sessions to verify no regressions
5.3. Update CLAUDE.md acceptable baseline if any errors remain
5.4. Verify code formatting with `poetry run nox -s format` and `poetry run nox -s lint`
5.5. Move feature document to `docs/features/completed/`
5.6. Final commit with all changes

---

## Progress

- [x] Milestone 1: Configure SQLAlchemy Mypy Plugin
- [x] Milestone 2: Migrate Models to SQLAlchemy 2.0 Mapped Types
- [x] Milestone 3: Fix Function Type Annotations
- [x] Milestone 4: Fix Type Mismatches in Views and API
- [x] Milestone 5: Acceptance Criteria

**COMPLETED** - All 110 mypy errors resolved, error count reduced to 0.
