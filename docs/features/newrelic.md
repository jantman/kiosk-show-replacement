# NewRelic and Deployment Docs

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

1. Set up optional NewRelic integration for this application. NewRelic should only be activated/loaded if the `NEW_RELIC_LICENSE_KEY` environment variable is set and non-empty. All NewRelic configuration should be via environment variables, not a `.ini` file. Document basic/minimal NewRelic configuration in `docs/deployment.rst`.
2. Update all relevant documentation (`docs/deployment.rst`, `docs/development.rst`, `docs/installation.rst`, `CLAUDE.md`, and `README.md`) to clarify that Docker is the only supported installation pattern for production deployments and local Python installation is only supported for development. Ensure that instructions for direct local (non-Docker) installation appear ONLY in `docs/development.rst` and `CLAUDE.md` and that all other (deployment, installation, README) documents only give instructions for Docker installation and clarify that this is the only supported method for production use.
