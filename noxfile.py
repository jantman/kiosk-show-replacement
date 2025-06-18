"""
Nox configuration for kiosk-show-replacement.

This file defines automated tasks for testing, linting, formatting,
and other development activities using nox.
"""

import nox

# Python versions to test against
PYTHON_VERSIONS = ["3.13"]
# Default Python version for development tasks
DEFAULT_PYTHON = "3.13"

# Locations of source code
PACKAGE_DIR = "kiosk_show_replacement"
TEST_DIR = "tests"
DOCS_DIR = "docs"


@nox.session(python=DEFAULT_PYTHON)
def format(session):
    """Format code with black and isort."""
    session.install("black", "isort")
    session.run("black", PACKAGE_DIR, TEST_DIR, "noxfile.py")
    session.run("isort", PACKAGE_DIR, TEST_DIR, "noxfile.py")


@nox.session(python=DEFAULT_PYTHON)
def lint(session):
    """Lint code with flake8 and pycodestyle."""
    session.install("flake8", "pycodestyle")
    session.run("flake8", PACKAGE_DIR, TEST_DIR)
    session.run("pycodestyle", "--max-line-length=88", PACKAGE_DIR, TEST_DIR)


@nox.session(python=DEFAULT_PYTHON, name="lint-frontend")
def lint_frontend(session):
    """Lint frontend code with ESLint and TypeScript."""
    import os

    frontend_dir = "frontend"

    # Check if frontend directory exists
    if not os.path.exists(frontend_dir):
        session.log("Frontend directory not found, skipping frontend linting")
        return

    # Check if Node.js and npm are available
    try:
        session.run("node", "--version", external=True)
        session.run("npm", "--version", external=True)
    except Exception as e:
        session.error(f"Node.js/npm not available: {e}")

    # Change to frontend directory
    session.chdir(frontend_dir)

    # Install dependencies if node_modules doesn't exist
    if not os.path.exists("node_modules"):
        session.log("Installing frontend dependencies...")
        session.run("npm", "install", external=True)

    # Run TypeScript type checking
    session.log("Running TypeScript type checking...")
    session.run("npm", "run", "type-check", external=True)

    # Run ESLint
    session.log("Running ESLint...")
    session.run("npm", "run", "lint", external=True)


@nox.session(python=DEFAULT_PYTHON, name="lint-all")
def lint_all(session):
    """Lint all code: backend (Python) and frontend (TypeScript/JavaScript)."""
    import os

    session.log("=== Running Comprehensive Linting ===")

    # 1. Lint backend code
    session.log("1. Linting backend code...")
    session.notify("lint")

    # 2. Lint frontend code if available
    if os.path.exists("frontend"):
        session.log("2. Linting frontend code...")
        session.notify("lint-frontend")
    else:
        session.log("2. Skipping frontend linting (frontend directory not found)")

    session.log("=== Comprehensive Linting Complete ===")


@nox.session(python=DEFAULT_PYTHON)
def type_check(session):
    """Type check with mypy."""
    session.install("mypy")
    # Install type stubs
    session.install("types-requests", "types-Flask-Cors", "types-Flask-Migrate")
    # Install package dependencies for type checking
    session.install("-e", ".")
    session.run("mypy", PACKAGE_DIR)


@nox.session(python=PYTHON_VERSIONS, name="test")
def test(session):
    """Run unit tests with pytest."""
    session.install("-e", ".")
    session.install("pytest", "pytest-cov", "pytest-flask", "pytest-mock")

    # Run tests with coverage
    session.run(
        "pytest",
        TEST_DIR + "/unit",
        "--cov=" + PACKAGE_DIR,
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-fail-under=30",
        "--durations=10",  # Show slowest 10 tests
        "-v",
        *session.posargs,
    )


def _find_system_chrome() -> str | None:
    """Find system Chrome/Chromium executable."""
    import os

    chrome_paths = [
        "/usr/bin/google-chrome-stable",  # Google Chrome on most Linux distros
        "/usr/bin/chromium-browser",  # Chromium on Ubuntu/Debian
        "/usr/bin/google-chrome",  # Alternative Chrome location
        "/usr/bin/chromium",  # Chromium on Arch/Fedora
    ]

    for path in chrome_paths:
        if os.path.exists(path):
            return path
    return None


@nox.session(python=DEFAULT_PYTHON, name="test-integration")
def test_integration(session):
    """Run integration tests: React frontend + Flask backend through real browser."""
    session.install("-e", ".")
    session.install(
        "pytest", "pytest-flask", "playwright", "pytest-playwright", "requests"
    )

    chrome_path = _find_system_chrome()

    if chrome_path:
        session.log(f"Using system Chrome at: {chrome_path}")
        # Set environment variable to use system Chrome
        session.env["PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"] = chrome_path

        # Run full-stack integration tests
        session.run(
            "pytest",
            TEST_DIR + "/integration",
            "--browser",
            "chromium",
            "--video",
            "retain-on-failure",
            "--screenshot",
            "only-on-failure",
            "-v",
            "-s",  # Don't capture output so we can see print statements
            *session.posargs,
        )
    else:
        session.log("Warning: No system Chrome found. Integration tests may fail.")
        session.log(
            "Checked paths: /usr/bin/google-chrome-stable, /usr/bin/chromium-browser, /usr/bin/google-chrome, /usr/bin/chromium"
        )
        # Try with the 'chrome' channel which might find system Chrome
        session.run(
            "pytest",
            TEST_DIR + "/integration",
            "--browser-channel",
            "chrome",
            "--video",
            "retain-on-failure",
            "--screenshot",
            "only-on-failure",
            "-v",
            "-s",
            *session.posargs,
        )


@nox.session(python=DEFAULT_PYTHON, name="test-e2e")
def test_e2e(session):
    """Run end-to-end tests: Flask server-rendered pages through browser automation."""
    session.install("-e", ".")
    session.install("pytest", "pytest-flask", "playwright", "pytest-playwright")

    chrome_path = _find_system_chrome()

    if chrome_path:
        session.log(f"Using system Chrome at: {chrome_path}")
        # Set environment variable to use system Chrome
        session.env["PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"] = chrome_path

        # Run E2E tests
        session.run(
            "pytest",
            TEST_DIR + "/e2e",
            "--browser",
            "chromium",
            "--video",
            "retain-on-failure",
            "--screenshot",
            "only-on-failure",
            "-v",
            *session.posargs,
        )
    else:
        session.log("Warning: No system Chrome found. E2E tests may fail.")
        session.log(
            "Checked paths: /usr/bin/google-chrome-stable, /usr/bin/chromium-browser, /usr/bin/google-chrome, /usr/bin/chromium"
        )
        # Try with the 'chrome' channel which might find system Chrome
        session.run(
            "pytest",
            TEST_DIR + "/e2e",
            "--browser-channel",
            "chrome",
            "--video",
            "retain-on-failure",
            "--screenshot",
            "only-on-failure",
            "-v",
            *session.posargs,
        )


@nox.session(python=DEFAULT_PYTHON, name="test-all")
def test_all(session):
    """Run all backend tests (unit only) with coverage. Integration and E2E tests run separately."""
    session.install("-e", ".")
    session.install("pytest", "pytest-cov", "pytest-flask", "pytest-mock")

    # Run only unit tests with coverage
    session.run(
        "pytest",
        TEST_DIR + "/unit",
        "--cov=" + PACKAGE_DIR,
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-fail-under=30",
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON, name="test-comprehensive")
def test_comprehensive(session):
    """Run all tests: backend unit tests, integration tests, frontend tests, and E2E tests."""
    import os

    session.log("=== Running Comprehensive Test Suite ===")

    # 1. Run backend unit tests
    session.log("1. Running backend unit tests...")
    session.notify("test-all")

    # 2. Run integration tests
    session.log("2. Running integration tests...")
    session.notify("test-integration")

    # 3. Run frontend tests if available
    if os.path.exists("frontend"):
        session.log("3. Running frontend tests...")
        session.notify("test-frontend")
    else:
        session.log("3. Skipping frontend tests (frontend directory not found)")

    # 4. Run E2E tests
    session.log("4. Running E2E tests...")
    session.notify("test-e2e")

    session.log("=== Comprehensive Test Suite Complete ===")
    session.log("Results:")
    session.log("- Backend unit tests: Check output above")
    session.log("- Integration tests: Check output above")
    session.log("- Frontend tests: Check output above")
    session.log("- E2E tests: Check output above")


@nox.session(python=DEFAULT_PYTHON, name="test-frontend")
def test_frontend(session):
    """Run frontend tests with Vitest."""
    import os
    import subprocess

    frontend_dir = "frontend"

    # Check if frontend directory exists
    if not os.path.exists(frontend_dir):
        session.log("Frontend directory not found, skipping frontend tests")
        return

    # Check if Node.js and npm are available
    try:
        session.run("node", "--version", external=True)
        session.run("npm", "--version", external=True)
    except Exception as e:
        session.error(f"Node.js/npm not available: {e}")

    # Change to frontend directory
    session.chdir(frontend_dir)

    # Install dependencies if node_modules doesn't exist
    if not os.path.exists("node_modules"):
        session.log("Installing frontend dependencies...")
        session.run("npm", "install", external=True)

    # Run frontend tests
    session.log("Running frontend tests with Vitest...")
    session.run("npm", "run", "test:run", external=True)


@nox.session(python=DEFAULT_PYTHON, name="test-frontend-watch")
def test_frontend_watch(session):
    """Run frontend tests in watch mode with Vitest."""
    import os

    frontend_dir = "frontend"

    # Check if frontend directory exists
    if not os.path.exists(frontend_dir):
        session.log("Frontend directory not found, skipping frontend tests")
        return

    # Check if Node.js and npm are available
    try:
        session.run("node", "--version", external=True)
        session.run("npm", "--version", external=True)
    except Exception as e:
        session.error(f"Node.js/npm not available: {e}")

    # Change to frontend directory
    session.chdir(frontend_dir)

    # Install dependencies if node_modules doesn't exist
    if not os.path.exists("node_modules"):
        session.log("Installing frontend dependencies...")
        session.run("npm", "install", external=True)

    # Run frontend tests in watch mode
    session.log("Running frontend tests in watch mode...")
    session.run("npm", "run", "test", external=True)


@nox.session(python=DEFAULT_PYTHON)
def safety(session):
    """Check dependencies for security vulnerabilities."""
    session.install("safety")
    session.run("safety", "check", "--json")


@nox.session(python=DEFAULT_PYTHON)
def docs(session):
    """Build documentation with Sphinx."""
    session.install("-e", ".")
    session.install("sphinx", "sphinx-rtd-theme", "sphinx-autodoc-typehints")

    session.chdir(DOCS_DIR)
    session.run("sphinx-build", "-b", "html", ".", "_build/html")


@nox.session(python=DEFAULT_PYTHON, name="docs-serve")
def docs_serve(session):
    """Build and serve documentation locally."""
    session.install("-e", ".")
    session.install(
        "sphinx", "sphinx-rtd-theme", "sphinx-autodoc-typehints", "sphinx-autobuild"
    )

    session.chdir(DOCS_DIR)
    session.run(
        "sphinx-autobuild", ".", "_build/html", "--host", "0.0.0.0", "--port", "8000"
    )


@nox.session(python=DEFAULT_PYTHON)
def clean(session):
    """Clean up build artifacts and cache files."""
    import os
    import shutil

    directories_to_clean = [
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "htmlcov",
        "build",
        "dist",
        "*.egg-info",
        DOCS_DIR + "/_build",
    ]

    for pattern in directories_to_clean:
        if "*" in pattern:
            # Handle glob patterns
            import glob

            for path in glob.glob(pattern, recursive=True):
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                    session.log(f"Removed directory: {path}")
        else:
            # Handle direct directory paths
            for root, dirs, files in os.walk("."):
                if pattern in dirs:
                    dir_path = os.path.join(root, pattern)
                    shutil.rmtree(dir_path, ignore_errors=True)
                    session.log(f"Removed directory: {dir_path}")


@nox.session(python=DEFAULT_PYTHON, name="dev-setup")
def dev_setup(session):
    """Set up development environment."""
    import os

    # Install Python dependencies
    session.install("-e", ".")
    session.install(
        "black",
        "isort",
        "flake8",
        "pycodestyle",
        "mypy",
        "pytest",
        "pytest-cov",
        "pytest-flask",
        "pytest-mock",
    )

    # Initialize database
    session.run("kiosk-init-db", "--sample-data")

    # Set up frontend dependencies if frontend directory exists
    if os.path.exists("frontend"):
        session.log("Setting up frontend dependencies...")
        session.chdir("frontend")
        try:
            session.run("npm", "install", external=True)
            session.log("Frontend dependencies installed successfully!")
        except Exception as e:
            session.log(f"Warning: Could not install frontend dependencies: {e}")
            session.log("Make sure Node.js and npm are installed")
        session.chdir("..")

    session.log("Development environment setup complete!")
    session.log("Available commands:")
    session.log("  Backend:")
    session.log("    nox -s format          # Format code")
    session.log("    nox -s lint            # Check code style")
    session.log("    nox -s test            # Run unit tests")
    session.log("    nox -s test-integration # Run integration tests")
    session.log("    nox -s test-e2e        # Run E2E tests")
    session.log("    nox -s test-all        # Run all backend tests")
    if os.path.exists("frontend"):
        session.log("  Frontend:")
        session.log("    nox -s test-frontend   # Run frontend tests")
        session.log("    nox -s test-frontend-watch # Run frontend tests in watch mode")
    session.log("  Comprehensive:")
    session.log(
        "    nox -s test-comprehensive # Run all tests (backend + frontend + E2E)"
    )


# Default session when no session is specified
nox.options.sessions = ["format", "lint", "test"]
