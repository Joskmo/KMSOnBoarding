# syntax=docker/dockerfile:1

# -------------------------------
# Stage 1: Builder — install deps
# -------------------------------
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv

# Install dependencies into .venv (frozen = strict lockfile)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# -------------------------------
# Stage 2: Runtime — minimal image
# -------------------------------
FROM python:3.13-slim

WORKDIR /app

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy only application code and migrations
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Set proper ownership
RUN chown -R appuser:appgroup /app

# Activate venv via PATH (no need for uv in runtime)
ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
