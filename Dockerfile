# ---- builder: устанавливаем зависимости и формируем .venv ----
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Настройки uv (сборка байт-кода, режим копирования зависимостей)
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TOOL_BIN_DIR=/usr/local/bin

# Копируем только манифесты зависимостей для кэшируемой установки
COPY pyproject.toml uv.lock /app/

# Собираем зависимости проекта в .venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Копируем исходники и устанавливаем проект (если нужен локальный пакет)
COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# ---- runtime: минимальный образ с готовой виртуальной средой ----
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS runtime

WORKDIR /app

# Копируем готовый проект/venv из билдера
COPY --from=builder /app /app

# Гарантируем, что исполняемые файлы виртуального env видимы первыми в PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

# Порт приложения
EXPOSE 8000

# Запуск в production (uvicorn без hot-reload)
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
