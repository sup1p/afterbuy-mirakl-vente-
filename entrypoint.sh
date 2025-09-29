#!/bin/sh
set -e

# Краткое ожидание БД и применение миграций, затем запуск uvicorn.
# Требует, чтобы все зависимости (asyncpg, alembic, uv и т.д.) были в образе.

echo "EntryPoint: waiting for DATABASE..."

# Проверим переменные окружения
: "${DATABASE_URL:?DATABASE_URL must be set}"
DB_CHECK_URL="$DATABASE_URL"

# asyncpg не принимает префикс postgresql+asyncpg:// — уберём его для проверки соединения
PY_DSN=$(python - <<'PY'
import os
dsn = os.environ.get("DATABASE_URL")
if dsn is None:
    print("")
else:
    if dsn.startswith("postgresql+asyncpg://"):
        print(dsn.replace("postgresql+asyncpg://", "postgresql://", 1))
    else:
        print(dsn)
PY
)

if [ -z "$PY_DSN" ]; then
  echo "No DSN available for check, exiting"
  exit 1
fi

# Python-скрипт ждёт, пока БД будет доступна через asyncpg
python - <<'PY'
import os, time, asyncio
import asyncpg

dsn = os.getenv("DATABASE_URL")
if dsn is None:
    raise SystemExit("DATABASE_URL is not set")

# Подготовим DSN для asyncpg (убрать префикс +asyncpg)
if dsn.startswith("postgresql+asyncpg://"):
    dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)

print("Waiting for DB at:", dsn)
while True:
    try:
        conn = asyncio.get_event_loop().run_until_complete(asyncpg.connect(dsn))
        asyncio.get_event_loop().run_until_complete(conn.close())
        print("Database is ready")
        break
    except Exception as e:
        print("DB is not ready yet:", e)
        time.sleep(1)
PY

# Применяем миграции Alembic (если alembic доступен в PATH)
echo "Applying alembic migrations..."
alembic upgrade head

echo "Ensuring admin user exists..."
uv run python -m src.utils.create_admin

# Запускаем приложение (используем uv из образа)
echo "Starting uvicorn..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000



