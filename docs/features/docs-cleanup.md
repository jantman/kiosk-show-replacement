# Documentation Cleanup

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

The documentation for this project has grown organically over time and is now both duplicative and not well organized.

* We have Sphinx `.rst` docs in `docs/` and a `nox` session to build them, but we're not deploying them to GitHub Pages via github actions like we should.
* The README includes a mix of project structure, API endpoints, and installation docs.
* The `.rst` documents also have overlap.

We need to do the following:

1. Update the `Create Release` job of `.github/workflows/release.yml` so that it also builds the Sphinx documentation and deploys it to GitHub Pages.
2. Update the README.md so that is just contains a high-level description of the project and its features, contributing information, and license, and contains a prominent link near the top of the README to the github pages site for full documentation.
3. Ensure that `docs/api.rst` provides accurate and up-to-date API documentation, and that no API documentation appears in other documentation files; they should link to this file.
4. Remove the `docs/getting-started.rst` and `docs/installation.rst` pages in favor of `docs/deployment.rst`; any relevant information on the getting-started or installation pages that isn't already on the deployment page, should be added to it.
5. Update `docs/usage.rst` so that it just covers normal usage of the application via the frontend: adding/editing/managing slideshows, slides, and displays, and managing users (for admins). Keep the information on video formats and conversion, text slide formatting, and Skedda. Remove the information on API usage (this should go in `api.rst`), database management (this should be handled automatically by the Docker image), and the development server (this is for development only).

Finally, update `docs/index.rst` as needed for the above changes, and then ensure the `docs` nox environment runs successfully.
