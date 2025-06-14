Kiosk Show Replacement
======================

A self-hosted replacement for kiosk.show - a web application for managing and displaying slideshow presentations on kiosk displays.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
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

1. Install the application:

   .. code-block:: bash

      pip install kiosk-show-replacement

2. Initialize the database:

   .. code-block:: bash

      kiosk-init-db --sample-data

3. Run the development server:

   .. code-block:: bash

      python run.py

4. Open your browser to `http://localhost:5000`

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
