# Admin Integration Tests

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

In `tests/integration/test_full_user_experience.py` we have an integration test (full browser test of the actual React frontend and Flask backend) that claims to test the "complete user experience" but this really only tests the ability to login and see the dashboard. We need to first specify and then implement integration tests for the full functionality of the admin interface, including flows such as adding, editing, and managing slideshows, adding, editing, managing, and rearranging slideshow items (including uploading items of each supported type), managing displays and assigning slideshows to them, and all other user flows supported by the admin interface.

We should identify a list of user flows supported by the admin interface of the application and then specify and implement a test for each of them.

It is important to note that this application is very early in its development phase and many critical flows may currently be broken; so when we run the tests, we cannot assume that any test failures are a problem with the test, it may have found a legitimate problem with the application.

These tests are scoped to the admin functionality only; the display functionality will be tested in a future feature.
