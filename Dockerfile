FROM python:3.12-slim AS uv-base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

FROM uv-base AS dependencies
WORKDIR /app
ENV UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM dependencies AS dev-dependencies
RUN uv sync --frozen

# ローカル開発用 (Socket Mode)
FROM dev-dependencies AS local
ENV PYTHONUNBUFFERED=1
CMD ["uv", "run", "watchfiles", "python -m src.main", "src/"]

# 本番用ランタイム
FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=dependencies /app/.venv /app/.venv
COPY ./src ./src
COPY ./migrations ./migrations
EXPOSE 8080
CMD ["sh", "-c", "python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]