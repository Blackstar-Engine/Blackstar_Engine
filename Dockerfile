# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

# ---------- Environment ----------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# ---------- System dependencies ----------
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    tini \
    && rm -rf /var/lib/apt/lists/*

# ---------- Non-root runtime ----------
RUN useradd -m -u 1000 botuser
WORKDIR /app
RUN chown botuser:botuser /app

# ---------- Dependency layer (for fast rebuilds) ----------
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ---------- Application layer ----------
COPY --chown=botuser:botuser . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---------- Runtime ----------
USER botuser
ENTRYPOINT ["/usr/bin/tini", "--"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

CMD ["uv", "run", "python", "-m", "main"]
