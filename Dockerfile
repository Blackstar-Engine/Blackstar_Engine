# 1. Grab the uv binary from the official image
FROM ghcr.io/astral-sh/uv:latest AS uv

# 2. Start the main image
FROM python:3.12-slim

# Copy uv binaries into the slim image
COPY --from=uv /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Compile bytecode for faster startup
    UV_COMPILE_BYTECODE=1 \
    # Where the venv will live
    VIRTUAL_ENV=/app/.venv

# Update PATH so 'python' automatically uses the venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
# --mount=type=cache uses Docker's build cache for uv, making re-builds instant
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv && \
    uv pip install -r requirements.txt

# Copy the bot code
COPY . .

# Run the bot
# Because we updated PATH above, this uses the venv python automatically
CMD ["python", "-m", "main"]