# GitHub Copilot Instructions for kiosk-show-replacement

## Code Quality and Best Practices

### Resource Management
- **NEVER filter out warnings** - All warnings must be investigated and fixed at their source
- Always properly close database connections, file handles, and other resources
- Use context managers (`with` statements) for resource management when possible
- Explicitly call `.close()`, `.dispose()`, or similar cleanup methods when context managers aren't available

### Database and SQLAlchemy
- Always close database sessions after use: `db.session.close()`
- Use `try/finally` blocks to ensure cleanup happens even if exceptions occur
- Dispose of SQLAlchemy engines properly: `db.engine.dispose()`
- Never rely on garbage collection to clean up database connections
- Use NullPool for tests to prevent connection pooling issues

### Testing
- Fix ResourceWarnings by identifying and closing unclosed resources
- Do NOT use `warnings.filterwarnings()` to suppress warnings
- Do NOT use explicit `gc.collect()` to mask resource management problems
- Test fixtures should properly clean up resources they create
- Each test should be independent and not leak resources to other tests

### Python Best Practices
- Avoid explicit garbage collection (`gc.collect()`) - it usually indicates poor resource management
- Use proper exception handling with cleanup in `finally` blocks
- Follow the principle: "Fix the cause, not the symptom"
- Write defensive code that handles edge cases gracefully

### Error Handling
- Always investigate the root cause of warnings and errors
- Don't suppress exceptions or warnings without understanding why they occur
- Log meaningful error messages that help with debugging
- Use specific exception types rather than broad `except Exception` catches

## Project-Specific Guidelines

### Flask Application
- Use proper application context management
- Clean up Flask test clients and contexts after tests
- Ensure database sessions are scoped correctly to request lifecycles

### SQLite Connections
- Be especially careful with SQLite connections in tests
- Use `check_same_thread=False` only when necessary and document why
- Always close connections explicitly, especially in test environments

## Command Execution Requirements
- **ALWAYS run tests via `poetry run nox -s test`** - Never run pytest directly
- **ALL project commands must be run via `poetry`** - This ensures proper dependency management and virtual environment isolation
- Examples:
  - Tests: `poetry run nox -s test`
  - Linting: `poetry run nox -s lint` 
  - Install dependencies: `poetry install`
  - Add dependencies: `poetry add <package>`
  - Shell: `poetry shell`

## When Contributing Code
- Run tests with all warnings enabled to catch resource leaks
- Fix any ResourceWarnings before submitting code
- Write tests that verify proper resource cleanup
- Document any complex resource management patterns
- Code reviews should specifically check for proper resource management

## Examples of What NOT to Do
```python
# ❌ DON'T suppress warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

# ❌ DON'T force garbage collection to mask problems
gc.collect()

# ❌ DON'T leave resources unclosed
connection = create_connection()
# ... use connection without closing it
```

## Examples of What TO Do
```python
# ✅ DO use context managers
with create_connection() as connection:
    # ... use connection
    pass  # automatically closed

# ✅ DO use try/finally for explicit cleanup
connection = None
try:
    connection = create_connection()
    # ... use connection
finally:
    if connection:
        connection.close()

# ✅ DO clean up in test fixtures
@pytest.fixture
def sample_data():
    # Create test data
    data = create_test_data()
    yield data
    # Clean up
    cleanup_test_data(data)
```

Remember: **Quality code manages resources explicitly and handles errors gracefully. Warnings are signals of potential problems - fix them, don't hide them.**
