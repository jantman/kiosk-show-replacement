Installation
============

System Requirements
-------------------

* Python 3.9 or higher
* SQLite 3
* Modern web browser for management interface

Installation Methods
--------------------

Using Poetry (Recommended for Development)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/jantman/kiosk-show-replacement.git
      cd kiosk-show-replacement

2. Install dependencies and activate environment:

   .. code-block:: bash

      poetry install
      eval $(poetry env activate)

3. Initialize the database:

   .. code-block:: bash

      kiosk-init-db --sample-data

4. Run the development server:

   .. code-block:: bash

      python run.py

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
