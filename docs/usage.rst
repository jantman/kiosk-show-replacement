Usage
=====

Web Interface
-------------

Management Interface
~~~~~~~~~~~~~~~~~~~~

The main management interface is available at the root URL of your application (e.g., ``http://localhost:5000``).

Creating Slideshows
~~~~~~~~~~~~~~~~~~~~

1. Navigate to the main page
2. Click "Create New Slideshow"
3. Enter a name and description
4. Add slides with images, videos, or web content
5. Configure display settings (duration, transitions, etc.)

Managing Slides
~~~~~~~~~~~~~~~

For each slideshow, you can:

* Add new slides
* Reorder slides by dragging and dropping
* Edit slide content and settings
* Remove slides
* Preview the slideshow

Kiosk Display Mode
~~~~~~~~~~~~~~~~~~

Access the full-screen kiosk display at ``/display/<slideshow_id>``:

* Full-screen slideshow display
* Automatic slide transitions
* Touch/click navigation
* Keyboard controls (space bar, arrow keys)

REST API
--------

The application provides a complete REST API for programmatic access.

Slideshow Endpoints
~~~~~~~~~~~~~~~~~~~

.. http:get:: /api/slideshows

   Get all slideshows

   **Response:**

   .. code-block:: json

      [
        {
          "id": 1,
          "name": "My Slideshow",
          "description": "A sample slideshow",
          "created_at": "2024-01-01T12:00:00Z",
          "slides": [...]
        }
      ]

.. http:post:: /api/slideshows

   Create a new slideshow

   **Request:**

   .. code-block:: json

      {
        "name": "New Slideshow",
        "description": "Description here"
      }

.. http:get:: /api/slideshows/(int:id)

   Get a specific slideshow

.. http:put:: /api/slideshows/(int:id)

   Update a slideshow

.. http:delete:: /api/slideshows/(int:id)

   Delete a slideshow

Slide Endpoints
~~~~~~~~~~~~~~~

.. http:get:: /api/slideshows/(int:slideshow_id)/slides

   Get all slides for a slideshow

.. http:post:: /api/slideshows/(int:slideshow_id)/slides

   Add a new slide to a slideshow

   **Request:**

   .. code-block:: json

      {
        "content_type": "image",
        "content_url": "https://example.com/image.jpg",
        "title": "Slide Title",
        "duration": 5000,
        "order": 1
      }

.. http:get:: /api/slides/(int:id)

   Get a specific slide

.. http:put:: /api/slides/(int:id)

   Update a slide

.. http:delete:: /api/slides/(int:id)

   Delete a slide

Command Line Interface
----------------------

The application includes several CLI commands:

Database Management
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Initialize database with sample data
   kiosk-init-db --sample-data

   # Reset database (drop and recreate tables)
   kiosk-init-db --reset

   # Import slideshow from JSON file
   kiosk-show import slideshow.json

   # Export slideshow to JSON file
   kiosk-show export 1 slideshow.json

Development Server
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run development server
   kiosk-show --debug

   # Run on specific host/port
   kiosk-show --host 0.0.0.0 --port 8080
