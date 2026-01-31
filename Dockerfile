# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Create non-root user
RUN groupadd -g 1000 botuser && \
    useradd -u 1000 -g botuser -m -s /bin/bash botuser

# Install system dependencies INCLUDING GIT
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (without the project itself)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY . .

# Install the project and set ownership
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Set default credentials path
ENV GOOGLE_APPLICATION_CREDENTIALS=/home/botuser/home/credentials.json

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD ["uv", "run", "python", "-c", "import sys; sys.exit(0)"]

# Run the bot
CMD ["uv", "run", "python", "-m", "main"]