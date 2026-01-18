# Multi-stage Dockerfile for kiosk-show-replacement
# Supports both amd64 and arm64 architectures

# =============================================================================
# Stage 1: Build frontend assets
# =============================================================================
FROM node:25.3.0-alpine3.23 AS frontend-build

WORKDIR /app/frontend

# Copy package files first for better layer caching
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci --no-audit --no-fund

# Copy frontend source and build
# Override outDir since vite.config.ts uses a relative path outside the frontend dir
COPY frontend/ ./
RUN npm run build -- --outDir ./dist

# =============================================================================
# Stage 2: Python runtime
# =============================================================================
FROM python:3.14.2-slim-trixie AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
# - libmagic1: Required by python-magic for file type detection
# - curl: For health checks
# - netcat-openbsd: For database connectivity check in entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Install Poetry for dependency management
RUN pip install poetry==2.2.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Export dependencies to requirements.txt and install with pip
# This is more efficient than using poetry in production
RUN poetry export -f requirements.txt --without-hashes --only main > requirements.txt \
    && pip install -r requirements.txt \
    && rm -rf ~/.cache/pip

# Copy application code
COPY kiosk_show_replacement/ ./kiosk_show_replacement/
COPY migrations/ ./migrations/
COPY run.py flask_cli.py ./

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist ./kiosk_show_replacement/static/dist/

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create instance directory for uploads and SQLite database
RUN mkdir -p /app/instance/uploads \
    && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Set the entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command: run with gunicorn using eventlet worker
CMD ["gunicorn", "--worker-class", "eventlet", "--workers", "2", "--bind", "0.0.0.0:5000", "--timeout", "120", "kiosk_show_replacement.app:create_app('production')"]
