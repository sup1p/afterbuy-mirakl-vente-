# ---- builder: устанавливаем зависимости и формируем .venv ----
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Настройки uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TOOL_BIN_DIR=/usr/local/bin

# Копируем только манифесты зависимостей для кэшируемой установки
COPY pyproject.toml uv.lock /app/

# Сборка зависимостей проекта в .venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

# Копируем весь проект после создания .venv
COPY . /app

# Устанавливаем проект (локальный пакет, если нужен)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

# ---- runtime: минимальный образ с готовой виртуальной средой ----
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS runtime

WORKDIR /app

# Копируем готовый проект/venv из билдера
COPY --from=builder /app /app

RUN mkdir -p /app/logs/logs && [ -f /app/logs/logs/logs.log ] || touch /app/logs/logs/logs.log

# Делаем entrypoint.sh исполняемым
RUN chmod +x /app/entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

EXPOSE 8301

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8301"]
