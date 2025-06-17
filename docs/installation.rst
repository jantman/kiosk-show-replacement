Installation
============

System Requirements
-------------------

* Python 3.9 or higher
* SQLite 3
* Node.js 18.0 or higher and npm (for the React admin interface)
* Modern web browser for management interface

Installation Methods
--------------------

Using Poetry (Recommended for Development)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/jantman/kiosk-show-replacement.git
      cd kiosk-show-replacement

2. Install Python dependencies and activate environment:

   .. code-block:: bash

      poetry install
      eval $(poetry env activate)

3. Install Node.js dependencies for the React admin interface:

   .. code-block:: bash

      cd frontend
      npm install
      cd ..

4. Initialize the database:

   .. code-block:: bash

      kiosk-init-db --sample-data

5. Build the React frontend for production:

   .. code-block:: bash

      cd frontend
      npm run build
      cd ..

6. Run the application:

   .. code-block:: bash

      python run.py

The application will be available at:

* **Admin Interface**: http://localhost:5000/admin
* **API**: http://localhost:5000/api/v1/
* **Display Mode**: http://localhost:5000/display/<display-name>

Development Mode (With Frontend Hot Reload)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For frontend development with hot reload:

1. Follow steps 1-4 above (skip step 5 - no need to build)

2. Start the Flask backend:

   .. code-block:: bash

      python run.py

3. In a separate terminal, start the React development server:

   .. code-block:: bash

      cd frontend
      npm run dev

This will start:

* **Flask Backend**: http://localhost:5000 (API and display endpoints)
* **React Frontend**: http://localhost:3000 (Admin interface with hot reload)

The React dev server automatically proxies API requests to Flask.

Using pip
~~~~~~~~~

1. Install the package:

   .. code-block:: bash

      pip install kiosk-show-replacement

2. Initialize the database:

   .. code-block:: bash

      kiosk-init-db --sample-data

3. Run the application:

   .. code-block:: bash

      kiosk-show

Configuration
-------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

The application can be configured using environment variables:

* ``FLASK_ENV``: Set to ``development`` for development mode
* ``DATABASE_URL``: Database connection string (defaults to SQLite)
* ``SECRET_KEY``: Flask secret key for sessions
* ``UPLOAD_FOLDER``: Directory for uploaded files
* ``MAX_CONTENT_LENGTH``: Maximum file upload size

Database Initialization
~~~~~~~~~~~~~~~~~~~~~~~

The application requires database initialization before first use.

**Important**: First activate your Poetry environment (once per terminal session):

.. code-block:: bash

   eval $(poetry env activate)

Then run the initialization commands:

.. code-block:: bash

   # Initialize empty database
   kiosk-init-db

   # Initialize with sample data
   kiosk-init-db --sample-data

   # Drop existing tables and recreate
   kiosk-init-db --reset

Troubleshooting Installation
----------------------------

Common Issues
~~~~~~~~~~~~~

**Node.js/npm not found:**

If you get "node: command not found" or "npm: command not found":

.. code-block:: bash

   # Ubuntu/Debian
   sudo apt update
   sudo apt install nodejs npm

   # macOS with Homebrew
   brew install node

   # Or install Node.js from https://nodejs.org/

**Python/Poetry issues:**

If Poetry is not installed:

.. code-block:: bash

   # Install Poetry
   curl -sSL https://install.python-poetry.org | python3 -

   # Add to PATH (follow Poetry installation instructions)
   export PATH="$HOME/.local/bin:$PATH"

**Permission issues:**

If you encounter permission errors:

.. code-block:: bash

   # For npm packages, avoid sudo and use npx
   npx npm install

   # Or configure npm to use a different directory
   npm config set prefix ~/.npm-global
   export PATH=~/.npm-global/bin:$PATH

**Database initialization fails:**

.. code-block:: bash

   # Remove existing database and try again
   rm -f kiosk_show.db
   kiosk-init-db --sample-data

**Frontend build fails:**

.. code-block:: bash

   # Clear npm cache and reinstall
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build

Verifying Installation
~~~~~~~~~~~~~~~~~~~~~~

After installation, verify everything works:

.. code-block:: bash

   # Check Python environment
   eval $(poetry env activate)
   python -c "import kiosk_show_replacement; print('Backend OK')"

   # Check Node.js dependencies
   cd frontend
   npm list --depth=0

   # Check database
   kiosk-init-db --sample-data
   python -c "from kiosk_show_replacement.models import Slideshow; print(f'Slideshows: {len(Slideshow.query.all())}')"

   # Build frontend
   npm run build
   ls -la ../kiosk_show_replacement/static/dist/

   # Start application
   cd ..
   python run.py

Requirements Details
~~~~~~~~~~~~~~~~~~~~

**Minimum Versions:**
* Python: 3.9+
* Node.js: 18.0+
* npm: 8.0+
* SQLite: 3.31+

**Recommended Versions:**
* Python: 3.11+
* Node.js: 20.0+
* npm: 10.0+

**Disk Space:**
* ~50MB for Python dependencies
* ~200MB for Node.js dependencies
* ~1MB for SQLite database (grows with content)

**Memory:**
* Minimum: 512MB RAM
* Recommended: 1GB+ RAM for development

**Network:**
* Internet connection required for initial dependency installation
* No internet required for operation after installation
