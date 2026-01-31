# syntax=docker/dockerfile:1

# 1. Use the official UV image with Python 3.12 (Stable)
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# 2. Set Env Vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# 3. Create non-root user
RUN groupadd -g 1000 interchat && \
    useradd -u 1000 -g interchat -m -s /bin/bash interchat

# 4. Install Git (Required for discord.py from GitHub)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    git build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 5. Copy requirements
COPY requirements.txt .

# 6. Install dependencies using 'uv pip' (Compatible with requirements.txt)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv && \
    uv pip install -r requirements.txt

# 7. Copy your code
COPY . .

# 8. Set permissions
RUN chown -R interchat:interchat /app

USER interchat

# 9. Run the bot
CMD ["python", "-m", "main"]