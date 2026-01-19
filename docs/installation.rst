Installation
============

This guide covers installing kiosk-show-replacement for production use.

.. note::

   **Docker is the only supported installation method for production.**

   For local development setup (Python/Poetry), see :doc:`development`.

System Requirements
-------------------

* Docker Engine 20.10 or higher
* Docker Compose 2.0 or higher
* 512MB+ RAM (1GB+ recommended)
* 1GB+ disk space

The application supports both x86_64 and ARM64 architectures, including
Raspberry Pi 4 and newer.

Quick Start with Docker
-----------------------

1. **Clone the repository:**

   .. code-block:: bash

      git clone https://github.com/jantman/kiosk-show-replacement.git
      cd kiosk-show-replacement

2. **Configure environment:**

   .. code-block:: bash

      # Copy the example environment file
      cp .env.docker.example .env

      # Generate a secure secret key
      python -c "import secrets; print(secrets.token_hex(32))"

      # Edit .env and set your passwords
      # Required: SECRET_KEY, MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD, KIOSK_ADMIN_PASSWORD

3. **Start the application:**

   .. code-block:: bash

      # Production (with MariaDB)
      docker-compose -f docker-compose.prod.yml up -d

4. **Access the application:**

   * **Admin Interface**: http://localhost:5000/admin
   * **API**: http://localhost:5000/api/v1/

Default admin credentials are ``admin``/``admin`` unless you set
``KIOSK_ADMIN_PASSWORD`` in your environment.

Verifying Installation
----------------------

Check the application health:

.. code-block:: bash

   curl http://localhost:5000/health

Check container status:

.. code-block:: bash

   docker-compose -f docker-compose.prod.yml ps

View logs:

.. code-block:: bash

   docker-compose -f docker-compose.prod.yml logs -f app

Next Steps
----------

* See :doc:`deployment` for production configuration, environment variables,
  monitoring setup, and upgrade procedures.

* See :doc:`development` for local development setup without Docker.
