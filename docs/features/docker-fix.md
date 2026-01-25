# Docker Fix

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

The Docker image currently fails to build. We need to fix that, and then verify that both docker-compose files (`docker-compose.yml`) and (`docker-compose.prod.yml`) function correctly (i.e. that if we run each of these via docker compose, the application runs and we can log in to the admin UI and make some changes, which get persisted to the database).
