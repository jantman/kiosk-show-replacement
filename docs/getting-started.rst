Getting Started
===============

This guide will help you quickly set up and run the Kiosk Show Replacement application.

Quick Setup
-----------

1. Prerequisites
~~~~~~~~~~~~~~~~

Ensure you have the following installed:

* **Python 3.9+** with pip
* **Poetry** (Python dependency manager)
* **Node.js 18.0+** and **npm** (for the React admin interface)
* **Git** (to clone the repository)

**Install Poetry (if needed):**

.. code-block:: bash

   curl -sSL https://install.python-poetry.org | python3 -

**Install Node.js (if needed):**

* Download from https://nodejs.org/
* Or use your system package manager (apt, brew, dnf, etc.)

2. Clone and Setup
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/jantman/kiosk-show-replacement.git
   cd kiosk-show-replacement

   # Install Python dependencies
   poetry install
   eval $(poetry env activate)

   # Install Node.js dependencies
   cd frontend
   npm install
   cd ..

   # Initialize database with sample data
   kiosk-init-db --sample-data

   # Build the React admin interface
   cd frontend
   npm run build
   cd ..

3. Run the Application
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start the application
   python run.py

4. Access the Application
~~~~~~~~~~~~~~~~~~~~~~~~~

Open your web browser and visit:

* **🎛️ Admin Interface**: http://localhost:5000/admin

  * **Login**: ``admin`` / ``admin`` (change in production!)
  * Modern React-based admin panel
  
* **📊 Legacy Interface**: http://localhost:5000

  * Original Flask-based interface
  
* **🔌 API**: http://localhost:5000/api/v1/

  * REST API documentation

* **📺 Display Mode**: http://localhost:5000/display/<display-name>

  * Full-screen slideshow display

Development Mode
----------------

For frontend development with hot reload:

Terminal 1: Flask Backend
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   eval $(poetry env activate)
   python run.py

Terminal 2: React Frontend
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd frontend
   npm run dev

**Access:**

* **Backend API**: http://localhost:5000
* **Frontend Dev Server**: http://localhost:3000

What's Next?
------------

1. **📚 Read the Documentation**: Check out ``docs/`` for comprehensive guides
2. **👥 Create Users**: Use the admin interface to create additional users
3. **🖼️ Create Slideshows**: Start building your digital signage content
4. **📱 Setup Displays**: Configure and assign slideshows to displays
5. **🔧 Customize**: Modify settings and appearance to fit your needs

Quick Commands Reference
------------------------

.. code-block:: bash

   # Environment activation (run once per terminal session)
   eval $(poetry env activate)

   # Database operations
   kiosk-init-db --sample-data  # Initialize with sample data
   kiosk-init-db --reset        # Reset database

   # Development
   python run.py                # Start Flask server
   cd frontend && npm run dev   # Start React dev server

   # Testing
   nox -s test                  # Backend tests
   cd frontend && npm test      # Frontend tests

   # Code quality
   nox -s format               # Format backend code
   nox -s lint                 # Lint backend code
   cd frontend && npm run type-check  # Frontend type checking

Troubleshooting
---------------

**Common Issues:**

1. **Port already in use**: Change the port in ``run.py`` or kill existing processes
2. **Permission errors**: Don't use ``sudo`` with npm; configure npm properly
3. **Database errors**: Try ``rm kiosk_show.db`` and re-run ``kiosk-init-db``
4. **Frontend build fails**: Clear cache with ``cd frontend && rm -rf node_modules package-lock.json && npm install``

**Need Help?**

* Check the full documentation in ``docs/``
* Look at the README.md for detailed information
* Check GitHub issues for known problems

Next Steps
----------

Once you have the application running:

1. **Login to Admin**: http://localhost:5000/admin (admin/admin)
2. **Explore the Dashboard**: Get familiar with the interface  
3. **Create Your First Slideshow**: Add some content
4. **Configure a Display**: Set up slideshow assignment
5. **Test Display Mode**: View your slideshow in full-screen mode

Happy digital signaging! 🖥️✨
