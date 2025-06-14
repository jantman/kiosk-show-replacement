API Reference
=============

This section provides detailed documentation for the REST API endpoints.

.. automodule:: kiosk_show_replacement.api
   :members:
   :undoc-members:
   :show-inheritance:

Error Responses
---------------

All API endpoints return consistent error responses:

.. code-block:: json

   {
     "error": "Error message",
     "code": 400,
     "details": {
       "field": "Additional error details"
     }
   }

Status Codes
~~~~~~~~~~~~

* ``200 OK``: Request successful
* ``201 Created``: Resource created successfully
* ``400 Bad Request``: Invalid request data
* ``404 Not Found``: Resource not found
* ``409 Conflict``: Resource conflict (e.g., duplicate name)
* ``500 Internal Server Error``: Server error

Authentication
--------------

Currently, the API does not require authentication. This may change in future versions.

Rate Limiting
-------------

No rate limiting is currently implemented. This may be added in future versions.

Content Types
-------------

All API endpoints accept and return JSON data with ``Content-Type: application/json``.
