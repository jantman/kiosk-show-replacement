# AI Copilot Instructions for kiosk-show-replacement

## Core Rules
- **NEVER suppress warnings/errors without human approval** - Fix root cause, not symptoms
- **Always use proper type annotations** on all new code
- **Always close resources explicitly** - Use context managers or try/finally
- **Environment must be activated once per terminal session** - Run `eval $(poetry env activate)` at the start of each new terminal session
- **Do not** run the same command multiple times in a row; if this will be needed, then use a temporary file to store the output and analyze it later, such as `cmd > file.txt 2>&1; analyze file.txt; rm -f file.txt`. Be sure to clean up the temporary file after analysis.
- **Always** include the `-f` option when removing files, such as `rm -f file.txt`.
- **Always** run the `format` nox session before running the `lint` session, such as `poetry run nox -s format; poetry run nox -s lint`.
- **Always** run tests via `nox`, not directly with `pytest` or `python -m pytest`.
- **Never** run the `lint` or `format` nox sessions with uncommitted git changes. Always commit changes before running these sessions.

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
# FIRST: Activate environment (once per terminal session)
eval $(poetry env activate)

# Then run commands normally (no poetry run prefix needed)
nox -s test

# Linting
nox -s lint

# Analysis pattern
nox -s lint > lint.txt 2>&1
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

## Testing Session Distinctions

### test-integration Session
- **Purpose**: Full-stack React frontend + Flask backend integration testing
- **Technology**: Playwright browser automation with dual server setup
- **Test Location**: `tests/integration/`
- **What it tests**: Complete user workflows through React admin interface
- **Server Setup**: Starts both Flask (backend) and Vite (frontend) servers
- **Use Cases**:
  - React component interaction with Flask APIs
  - Authentication flows through React frontend
  - Real-time features (SSE) in React admin interface
  - Frontend-backend data synchronization
  - Complete user journeys (login → dashboard → management)

### test-e2e Session  
- **Purpose**: Flask server-rendered pages testing (traditional web)
- **Technology**: Playwright browser automation with Flask server only
- **Test Location**: `tests/e2e/`
- **What it tests**: Traditional Flask Jinja2 templates and server-side functionality
- **Server Setup**: Starts only Flask server with template rendering
- **Use Cases**:
  - Basic server access and template rendering
  - Traditional Flask form submission
  - Server-side authentication workflows
  - Non-React page functionality
  - Flask route navigation and error handling

### Key Distinction Rule
- **Integration tests** = React frontend + Flask backend integration
- **E2E tests** = Flask backend only (traditional web pages)
- **SSE functionality** belongs in integration tests (React admin interface feature)
- **Basic server access** belongs in E2E tests (fundamental Flask functionality)
