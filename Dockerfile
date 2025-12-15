# 共通設定
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# ローカル開発用 (Socket Mode)
FROM base AS local
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
CMD ["uv", "run", "watchfiles", "python -m src.main", "src/"]

# 開発/本番環境用
FROM base AS runtime
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY ./src ./src
COPY ./migrations ./migrations
EXPOSE 8080
CMD ["uv", "run", "python", "-m", "src.main"]