Kiosk Show Replacement
======================

A self-hosted replacement for kiosk.show - a web application for managing and displaying slideshow presentations on kiosk displays.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   installation
   deployment
   usage
   api
   development
   modules

Features
--------

* **Web-based slideshow management**: Create and manage slideshows through a web interface
* **Kiosk display mode**: Full-screen slideshow display for kiosk installations
* **REST API**: Complete API for programmatic management of slideshows and slides
* **Multiple media types**: Support for images, videos, and web content
* **Responsive design**: Works on desktop, tablet, and mobile devices
* **SQLite database**: Simple, file-based database storage
* **Flask framework**: Built on the popular Flask web framework

Quick Start
-----------

**Complete Application Setup:**

1. **Install dependencies:**

   .. code-block:: bash

      # Clone repository
      git clone https://github.com/jantman/kiosk-show-replacement.git
      cd kiosk-show-replacement

      # Install Python dependencies
      poetry install
      eval $(poetry env activate)

      # Install Node.js dependencies
      cd frontend && npm install && cd ..

2. **Initialize database:**

   .. code-block:: bash

      FLASK_APP=kiosk_show_replacement.app poetry run flask cli init-db
      # Default credentials: admin / admin

3. **Build and run:**

   .. code-block:: bash

      # Build frontend
      cd frontend && npm run build && cd ..

      # Start application
      python run.py

4. **Access the application:**

   * **Admin Interface**: http://localhost:5000/admin (login: admin/admin)
   * **API Documentation**: http://localhost:5000/api/v1/
   * **Display Mode**: http://localhost:5000/display/<display-name>

**Development Mode (with hot reload):**

.. code-block:: bash

   # Terminal 1: Start Flask backend
   eval $(poetry env activate)
   python run.py

   # Terminal 2: Start React frontend
   cd frontend
   npm run dev

   # Access frontend at: http://localhost:3000

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
