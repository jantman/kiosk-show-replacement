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


@nox.session(python=DEFAULT_PYTHON)
def type_check(session):
    """Type check with mypy."""
    session.install("mypy")
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
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON, name="test-integration")
def test_integration(session):
    """Run integration tests with pytest."""
    session.install("-e", ".")
    session.install("pytest", "pytest-cov", "pytest-flask", "pytest-mock")

    session.run(
        "pytest",
        TEST_DIR + "/integration",
        "--cov=" + PACKAGE_DIR,
        "--cov-report=term-missing",
        "--cov-append",
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON, name="test-e2e")
def test_e2e(session):
    """Run end-to-end tests with pytest."""
    session.install("-e", ".")
    session.install("pytest", "pytest-flask", "pytest-mock", "selenium")

    session.run("pytest", TEST_DIR + "/e2e", *session.posargs)


@nox.session(python=DEFAULT_PYTHON, name="test-all")
def test_all(session):
    """Run all tests (unit, integration, e2e) with coverage."""
    session.install("-e", ".")
    session.install("pytest", "pytest-cov", "pytest-flask", "pytest-mock", "selenium")

    # Run all tests with combined coverage
    session.run(
        "pytest",
        TEST_DIR,
        "--cov=" + PACKAGE_DIR,
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-fail-under=30",  # Lower threshold for e2e included
        *session.posargs,
    )


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
    session.run("kiosk-init-db", "--sample-data")
    session.log("Development environment setup complete!")
    session.log("Run 'nox -s format' to format code")
    session.log("Run 'nox -s lint' to check code style")
    session.log("Run 'nox -s test' to run unit tests")


# Default session when no session is specified
nox.options.sessions = ["format", "lint", "test"]
