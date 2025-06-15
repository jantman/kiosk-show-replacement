Development
===========

Setting up tAvailable Commands
~~~~~~~~~~~~~~~~~~

**Important**: First activate your Poetry environment in any new terminal session:

.. code-block:: bash

   eval $(poetry env activate)

Then run the development commands:ment Environment
---------------------------------------

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/jantman/kiosk-show-replacement.git
      cd kiosk-show-replacement

2. Install Poetry (if not already installed):

   .. code-block:: bash

      curl -sSL https://install.python-poetry.org | python3 -

3. Install dependencies and activate environment:

   .. code-block:: bash

      poetry install
      eval $(poetry env activate)

4. Set up the development environment:

   .. code-block:: bash

      nox -s dev-setup

Development Workflow
--------------------

This project uses `nox <https://nox.thea.codes/>`_ for development automation.

Available Commands
~~~~~~~~~~~~~~~~~~

**Important**: First activate your Poetry environment in any new shell:

.. code-block:: bash

   eval $(poetry env activate)

Then run the development commands:

.. code-block:: bash

   # Format code with black and isort
   nox -s format

   # Run linting (flake8, pycodestyle)
   nox -s lint

   # Run type checking with mypy
   nox -s type_check

   # Run unit tests
   nox -s test

   # Run integration tests
   nox -s test-integration

   # Run end-to-end tests
   nox -s test-e2e

   # Run all tests with coverage
   nox -s test-all

   # Build documentation
   nox -s docs

   # Serve documentation locally
   nox -s docs-serve

   # Clean build artifacts
   nox -s clean

   # Check for security vulnerabilities
   nox -s safety

Default Development Session
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Running ``nox`` without arguments will run the default development session (format, lint, test):

.. code-block:: bash

   # After activating environment
   nox

Code Style
----------

This project uses several tools to maintain code quality:

* **Black**: Code formatting
* **isort**: Import sorting
* **flake8**: Linting and style checking
* **mypy**: Type checking

Configuration files:

* ``.flake8``: flake8 configuration
* ``pyproject.toml``: Black, isort, and mypy configuration

Testing
-------

The project uses pytest for testing with three types of tests:

**Important**: First activate your Poetry environment in any new terminal session:

.. code-block:: bash

   eval $(poetry env activate)

Unit Tests
~~~~~~~~~~

Located in ``tests/unit/``, these test individual functions and classes in isolation.

.. code-block:: bash

   nox -s test

Integration Tests
~~~~~~~~~~~~~~~~~

Located in ``tests/integration/``, these test the interaction between components.

.. code-block:: bash

   nox -s test-integration

End-to-End Tests
~~~~~~~~~~~~~~~~

Located in ``tests/e2e/``, these test complete user workflows.

.. code-block:: bash

   nox -s test-e2e

Test Configuration
~~~~~~~~~~~~~~~~~~

* ``pytest.ini``: Pytest configuration
* ``tests/conftest.py``: Shared test fixtures

Coverage
~~~~~~~~

Code coverage is measured using pytest-cov. Coverage reports are generated in:

* Terminal output (with ``--cov-report=term-missing``)
* HTML report in ``htmlcov/`` directory
* XML report as ``coverage.xml``

Database Testing
~~~~~~~~~~~~~~~~

Tests use an in-memory SQLite database for speed. The test database is automatically created and destroyed for each test session.

Project Structure
-----------------

.. code-block:: text

   kiosk-show-replacement/
   ├── kiosk_show_replacement/       # Main package
   │   ├── __init__.py
   │   ├── app.py                    # Flask application factory
   │   ├── api/                      # REST API blueprints
   │   ├── auth/                     # Authentication (future)
   │   ├── cli/                      # Command-line interface
   │   ├── config/                   # Configuration management
   │   ├── display/                  # Display/kiosk blueprints
   │   ├── models/                   # Database models
   │   ├── slideshow/                # Slideshow management
   │   ├── static/                   # Static files
   │   ├── templates/                # Jinja2 templates
   │   └── utils/                    # Utility functions
   ├── tests/                        # Test suite
   │   ├── unit/                     # Unit tests
   │   ├── integration/              # Integration tests
   │   └── e2e/                      # End-to-end tests
   ├── docs/                         # Documentation
   ├── scripts/                      # Utility scripts
   ├── noxfile.py                    # Development automation
   ├── pyproject.toml               # Poetry configuration
   └── README.md

Adding New Features
-------------------

1. Create a new branch for your feature
2. Write tests first (TDD approach)
3. Implement the feature
4. Run the full test suite
5. Update documentation
6. Submit a pull request

Database Migrations
-------------------

This project uses Flask-Migrate for database migrations.

**Important**: First activate your Poetry environment in any new terminal session:

.. code-block:: bash

   eval $(poetry env activate)

Then run migration commands:

.. code-block:: bash

   # Create a new migration
   flask db migrate -m "Description of changes"

   # Apply migrations
   flask db upgrade

   # Rollback migrations
   flask db downgrade

Contributing
------------

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Update documentation
7. Submit a pull request

Code Review Process
~~~~~~~~~~~~~~~~~~~

All contributions go through code review:

1. Automated checks (linting, testing, type checking)
2. Manual review by maintainers
3. Discussion and iteration
4. Approval and merge

Release Process
---------------

1. Update version in ``pyproject.toml``
2. Update ``CHANGELOG.md``
3. Create a Git tag
4. Build and publish to PyPI
5. Create GitHub release
