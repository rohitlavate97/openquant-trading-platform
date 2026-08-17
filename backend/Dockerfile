FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# Install uv for fast, reliable package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies first for Docker layer caching
COPY pyproject.toml .
RUN uv sync --frozen --no-install-project --no-dev

# Copy source code
COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "openquant.interfaces.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
