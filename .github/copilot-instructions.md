# AI Copilot Instructions for kiosk-show-replacement

## Core Rules
- **NEVER suppress warnings/errors without human approval** - Fix root cause, not symptoms
- **Always use proper type annotations** on all new code
- **Always close resources explicitly** - Use context managers or try/finally
- **All commands via poetry** - Tests: `poetry run nox -s test`, Lint: `poetry run nox -s lint`
- **Do not** run the same command multiple times in a row; if this will be needed, then use a temporary file to store the output and analyze it later, such as `cmd > file.txt 2>&1; analyze file.txt; rm -f file.txt`. Be sure to clean up the temporary file after analysis.
- **Always** include the `-f` option when removing files, such as `rm -f file.txt`.

## Resource Management
### Database/SQLAlchemy
- Close sessions: `db.session.close()`, Dispose engines: `db.engine.dispose()`
- Use NullPool for tests, always close SQLite connections explicitly
- Use try/finally blocks for cleanup

### Testing
- Fix ResourceWarnings at source, don't suppress with `warnings.filterwarnings()`
- Don't use `gc.collect()` to mask resource problems
- Test fixtures must cleanup resources they create

## Warning/Error Suppression Policy
**Requires explicit human approval before using:**
- `warnings.filterwarnings()`, `# type: ignore`, `# noqa`, `# pragma: no cover`
- Any pytest skip/ignore markers

**Approval process:**
1. Explain why can't fix at source
2. Document third-party library limitation
3. Prove functionality works despite warning/error
4. Propose minimal suppression scope

## Acceptable Baselines
### Type Checking (mypy): 11 errors acceptable
- SQLAlchemy/Flask-Migrate missing type stubs
- Third-party library limitations only

### Testing ResourceWarnings: ~28 expected
- Flask-SQLAlchemy: ~15-20 from connection pooling teardown
- pytest fixtures: ~5-8 from cleanup
- Werkzeug/Flask: ~3-5 from test client cleanup
- **Zero tolerance for application code ResourceWarnings**

## Command Examples
```bash
# Tests
poetry run nox -s test

# Analysis pattern
poetry run nox -s lint > lint.txt 2>&1
# analyze lint.txt
rm -f lint.txt

# Good resource management
with create_connection() as conn:
    # use conn
    pass  # auto-closed

# Test fixture cleanup
@pytest.fixture
def resource():
    data = create_resource()
    yield data
    cleanup_resource(data)
```
