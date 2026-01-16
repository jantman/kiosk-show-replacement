Deployment
==========

This guide covers deploying kiosk-show-replacement in production environments
using Docker.

Docker Deployment (Recommended)
-------------------------------

Docker provides the easiest and most reproducible deployment method. The
application supports both x86_64 and ARM64 architectures (including Raspberry Pi).

Quick Start
~~~~~~~~~~~

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/jantman/kiosk-show-replacement.git
      cd kiosk-show-replacement

2. Copy and configure the environment file:

   .. code-block:: bash

      cp .env.docker.example .env

3. Edit ``.env`` and set required values:

   .. code-block:: bash

      # Generate a secure secret key
      python -c "import secrets; print(secrets.token_hex(32))"

      # Edit .env with your values
      SECRET_KEY=<generated-key>
      MYSQL_ROOT_PASSWORD=<strong-password>
      MYSQL_PASSWORD=<strong-password>
      KIOSK_ADMIN_PASSWORD=<strong-password>

4. Start the application:

   .. code-block:: bash

      docker-compose -f docker-compose.prod.yml up -d

5. Access the application at http://localhost:5000/admin

Development with Docker
~~~~~~~~~~~~~~~~~~~~~~~

For development with Docker (using SQLite):

.. code-block:: bash

   # Start development environment
   docker-compose up

   # The application will be available at http://localhost:5000

This uses SQLite and mounts the source code for development visibility.

Production Configuration
------------------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Required variables for production:

========================= ==========================================
Variable                  Description
========================= ==========================================
``SECRET_KEY``            Flask secret key for session security
``MYSQL_ROOT_PASSWORD``   MariaDB root password
``MYSQL_PASSWORD``        MariaDB application user password
``KIOSK_ADMIN_PASSWORD``  Initial admin user password
========================= ==========================================

Optional variables (with defaults):

========================= ==========================================
Variable                  Default
========================= ==========================================
``APP_PORT``              5000
``MYSQL_DATABASE``        kiosk_show
``MYSQL_USER``            kiosk
``KIOSK_ADMIN_USERNAME``  admin
``KIOSK_ADMIN_EMAIL``     (none)
``GUNICORN_WORKERS``      2
========================= ==========================================

Database Configuration
~~~~~~~~~~~~~~~~~~~~~~

The application supports multiple database backends via the ``DATABASE_URL``
environment variable:

**SQLite** (development/single-node):

.. code-block:: bash

   DATABASE_URL=sqlite:///kiosk_show.db

**MariaDB/MySQL** (production):

.. code-block:: bash

   DATABASE_URL=mysql+pymysql://user:password@host:3306/database

**PostgreSQL**:

.. code-block:: bash

   DATABASE_URL=postgresql://user:password@host:5432/database

The production Docker Compose file automatically configures MariaDB.

Resource Limits
~~~~~~~~~~~~~~~

The production Docker Compose file includes resource limits:

**Application container:**

* CPU: 2 cores max, 0.5 cores reserved
* Memory: 1GB max, 256MB reserved

**Database container:**

* CPU: 1 core max, 0.25 cores reserved
* Memory: 512MB max, 128MB reserved

For Raspberry Pi deployments, consider reducing these limits:

.. code-block:: yaml

   # In docker-compose.prod.yml
   deploy:
     resources:
       limits:
         cpus: '1'
         memory: 512M

Production Checklist
--------------------

Before deploying to production:

1. **Security**

   * [ ] Generate a strong ``SECRET_KEY``
   * [ ] Set strong passwords for database and admin user
   * [ ] Review and restrict network access
   * [ ] Consider adding a reverse proxy (nginx, Caddy) with TLS

2. **Database**

   * [ ] Configure database backups
   * [ ] Consider using external managed database for critical deployments

3. **Monitoring**

   * [ ] Set up container health monitoring
   * [ ] Configure log aggregation if needed
   * [ ] Set up alerts for container failures

4. **Data Persistence**

   * [ ] Verify volume mounts are working
   * [ ] Test backup and restore procedures
   * [ ] Document recovery procedures

Upgrade Procedures
------------------

To upgrade to a new version:

1. **Backup your data**:

   .. code-block:: bash

      # Stop the application
      docker-compose -f docker-compose.prod.yml down

      # Backup database (MariaDB)
      docker-compose -f docker-compose.prod.yml run --rm db \
        mysqldump -u root -p$MYSQL_ROOT_PASSWORD $MYSQL_DATABASE > backup.sql

      # Backup uploads
      tar -czf uploads_backup.tar.gz ./data/uploads

2. **Pull new version**:

   .. code-block:: bash

      git pull origin main

3. **Rebuild and restart**:

   .. code-block:: bash

      docker-compose -f docker-compose.prod.yml build
      docker-compose -f docker-compose.prod.yml up -d

4. **Verify**:

   .. code-block:: bash

      # Check health
      curl http://localhost:5000/health

      # Check logs for errors
      docker-compose -f docker-compose.prod.yml logs -f app

Database migrations run automatically on container startup.

Troubleshooting
---------------

Container won't start
~~~~~~~~~~~~~~~~~~~~~

Check the logs:

.. code-block:: bash

   docker-compose -f docker-compose.prod.yml logs app

Common issues:

* **Missing environment variables**: Ensure all required variables are set
* **Database not ready**: The entrypoint waits up to 60 seconds for database
* **Port already in use**: Change ``APP_PORT`` or stop conflicting service

Database connection errors
~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify database is healthy:

.. code-block:: bash

   docker-compose -f docker-compose.prod.yml exec db \
     mysql -u root -p$MYSQL_ROOT_PASSWORD -e "SELECT 1"

Check database logs:

.. code-block:: bash

   docker-compose -f docker-compose.prod.yml logs db

Permission issues with uploads
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The container runs as non-root user (UID 1000). Ensure volume permissions:

.. code-block:: bash

   # Fix permissions on host
   sudo chown -R 1000:1000 ./data/uploads

Health check failing
~~~~~~~~~~~~~~~~~~~~

The health check uses ``/health`` endpoint:

.. code-block:: bash

   # Test manually
   curl http://localhost:5000/health

   # Check container health status
   docker inspect --format='{{.State.Health.Status}}' \
     $(docker-compose -f docker-compose.prod.yml ps -q app)

SQLite to MariaDB Migration
---------------------------

If you're migrating from a SQLite development database to MariaDB production:

1. **Export data from SQLite**:

   .. code-block:: bash

      # Using Flask shell
      flask shell
      >>> from kiosk_show_replacement.models import *
      >>> # Export your data using SQLAlchemy queries

2. **Start fresh with MariaDB**:

   The application will create tables and a default admin user automatically
   on first start.

3. **Re-import data** (if needed):

   Use the admin interface or API to recreate slideshows and content.

For large datasets, consider using database migration tools like ``pgloader``
or custom scripts.

Manual Deployment (Without Docker)
----------------------------------

If Docker is not available, you can deploy manually:

1. Install dependencies:

   .. code-block:: bash

      poetry install --without dev
      cd frontend && npm ci && npm run build && cd ..

2. Set environment variables:

   .. code-block:: bash

      export FLASK_ENV=production
      export SECRET_KEY=<your-secret-key>
      export DATABASE_URL=<your-database-url>

3. Initialize database:

   .. code-block:: bash

      flask db upgrade
      kiosk-init-db

4. Run with Gunicorn:

   .. code-block:: bash

      gunicorn --worker-class eventlet --workers 2 \
        --bind 0.0.0.0:5000 --timeout 120 \
        "kiosk_show_replacement.app:create_app('production')"

Note: The ``eventlet`` worker is required for Server-Sent Events (SSE) support.
