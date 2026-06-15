# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install basic build tools (in case any library requires compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and isolate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install and cache dependencies first using pyproject.toml
COPY pyproject.toml .

# Create a skeleton package to allow 'pip install .' to build dependency tree
RUN mkdir -p api config agents models chunkers indexers loaders parsers prompts providers services vectorstores && \
    touch api/__init__.py config/__init__.py agents/__init__.py models/__init__.py \
          chunkers/__init__.py indexers/__init__.py loaders/__init__.py parsers/__init__.py \
          prompts/__init__.py providers/__init__.py services/__init__.py vectorstores/__init__.py

# Install dependencies (only pyproject.toml updates bust this cache layer)
RUN pip install --no-cache-dir .


# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Create a non-root system group and user for security compliance
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -d /home/appuser -m -s /bin/bash appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Configure environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy source code and change ownership to non-root user
COPY --chown=appuser:appgroup . .

# Ensure all scripts are executable
RUN chmod +x scripts/startup.sh scripts/wait_for_qdrant.sh healthchecks/healthcheck.py

# Switch to non-root user
USER appuser

# Expose microservice HTTP port
EXPOSE 8000

# Docker healthcheck using the custom self-contained python healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 healthchecks/healthcheck.py

# Launch server
ENTRYPOINT ["/bin/sh", "scripts/startup.sh"]
