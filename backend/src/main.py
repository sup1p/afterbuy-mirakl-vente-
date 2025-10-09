"""
Основной модуль приложения FastAPI.
Обрабатывает жизненный цикл приложения, управление HTTP-клиентом и регистрацию маршрутов.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


from src.routers.vente.product_vente_router import router as product_vente_router
from src.routers.vente.mirakl_system_vente_router import router as mirakl_system_vente_router
from src.routers.vente.dev_vente_router import router as dev_vente_router 
from src.routers.vente.product_vente_from_file import router as product_vente_from_file_router

from src.routers.user_router import router as user_router
from src.routers.fabric_management import router as fabric_management_router

from src.routers.lutz.fabric_lutz_router import router as fabric_lutz_router
from src.routers.lutz.local_importer import router as local_importer_router
from src.routers.lutz.local_offers import router as local_offers_router
from src.routers.lutz.generate_csv_lutz_router import router as generate_csv_lutz_router
from src.routers.lutz.offers_lutz_router import router as offers_lutz_router
from src.routers.lutz.product_lutz_router import router as product_lutz_router

from src.services.vente_services.agents import create_agent_with_httpx
from src import resources
import logging
from logs.config_logs import setup_logging

import httpx
import asyncio

# Инициализация конфигурации логирования
setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Менеджер жизненного цикла приложения.
    Инициализирует HTTP-клиент и агента LLM при запуске,
    а также корректно закрывает их при завершении работы.
    """
    # --- запуск ---
    resources.client = httpx.AsyncClient(timeout=30.0)  # Инициализация HTTP-клиента
    resources.llm_semaphore = asyncio.Semaphore(8)  # Ограничение на количество одновременных запросов к LLM
    resources.ftp_semaphore = asyncio.Semaphore(8)  # Ограничение на количество FTP-запросов
    logger.info("Запуск: инициализированы семафоры для FTP и LLM")

    try:
        # Инициализируем глобальный агент (сохраняется в resources.llm_agent)
        await create_agent_with_httpx(
            resources.client
        )

        logger.info("Запуск: инициализированы HTTP-клиент, OpenAI-клиент и агент LLM")

        yield

    finally:
        # --- завершение ---
        try:
            if resources.openai_client:
                await resources.openai_client.close()
                logger.info("Завершение: OpenAI-клиент закрыт")
        except Exception:
            logger.exception("Завершение: ошибка при закрытии OpenAI-клиента")

        try:
            if resources.client:
                await resources.client.aclose()
                logger.info("Завершение: HTTP-клиент закрыт")
        except Exception:
            logger.exception("Завершение: ошибка при закрытии HTTP-клиента")

        # Очистка глобальных переменных
        resources.client = None
        resources.openai_client = None
        resources.llm_agent = None
        resources.llm_semaphore = None
        resources.ftp_semaphore = None

        logger.info("Завершение: ресурсы очищены")
    
# Создание приложения FastAPI с управлением жизненным циклом
app = FastAPI(lifespan=lifespan)

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # кому разрешаем
    allow_credentials=True,           # отправка куков / авторизации
    allow_methods=["*"],              # какие методы (GET, POST...) разрешены
    allow_headers=["*"],              # какие заголовки разрешены
)


@app.get("/", include_in_schema=False)
def root():
    """
    Эндпоинт для проверки работоспособности приложения.
    Возвращает сообщение, подтверждающее, что приложение запущено.
    """
    logger.info("Доступ к корневому эндпоинту")
    return "We are live!"

# Регистрация всех API-маршрутизаторов
# mutual
app.include_router(user_router)
app.include_router(fabric_management_router)

# vente
app.include_router(product_vente_from_file_router)
app.include_router(product_vente_router)
# app.include_router(mirakl_system_vente_router)
# app.include_router(dev_vente_router)

# lutz

# app.include_router(product_lutz_router)
# app.include_router(offers_lutz_router)
# app.include_router(generate_csv_lutz_router)
app.include_router(fabric_lutz_router)
app.include_router(local_importer_router)
app.include_router(local_offers_router)
