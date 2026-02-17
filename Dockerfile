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

# Install system dependencies (single layer, minimal packages)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (cache-friendly)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy application code with correct ownership (avoids chown layer)
COPY --chown=botuser:botuser . .

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Switch to non-root user
USER botuser

# Set default credentials path
ENV GOOGLE_APPLICATION_CREDENTIALS=/home/botuser/home/credentials.json

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD ["uv", "run", "python", "-c", "import sys; sys.exit(0)"]

# Run the bot
CMD ["uv", "run", "python", "-m", "main"]
