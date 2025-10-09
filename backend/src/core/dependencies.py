"""
Модуль внедрения зависимостей для FastAPI.
Предоставляет экземпляры HTTP-клиента для конечных точек API и управляет аутентификацией, сессиями базы данных и другими зависимостями.
"""

# Импорты из FastAPI для безопасности и зависимостей
from fastapi.security import OAuth2PasswordBearer  # Схема OAuth2 для аутентификации по токенам
from fastapi import Depends, HTTPException  # Depends для внедрения зависимостей, HTTPException для ошибок

# Импорты из локальных модулей
from src import resources  # Глобальные ресурсы приложения, такие как HTTP-клиент и LLM-агент
from src.core.settings import settings  # Настройки приложения, включая URL базы данных
from src.core.security import decode_access_token  # Функция для декодирования JWT-токенов
from src.crud.user import get_user_by_username  # CRUD-операция для получения пользователя по имени

# Импорты для работы с базой данных SQLAlchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession  # Асинхронный движок и сессия базы данных
from sqlalchemy.orm import sessionmaker  # Фабрика для создания сессий базы данных

# Импорты для обработки JWT и HTTP-запросов
from jose import JWTError  # Исключение для ошибок JWT
import httpx  # Библиотека для асинхронных HTTP-запросов

# Схема OAuth2 для Bearer-токенов, указывает URL для получения токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Создание асинхронного движка базы данных на основе URL из настроек
# future=True включает будущие версии SQLAlchemy, echo=False отключает логирование SQL-запросов
engine = create_async_engine(settings.database_url, future=True, echo=False)

# Фабрика сессий для асинхронной работы с базой данных
# expire_on_commit=False предотвращает истечение объектов после коммита
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_httpx_client() -> httpx.AsyncClient:
    """
    Возвращает глобальный экземпляр HTTP-клиента.
    Вызывает RuntimeError, если клиент не инициализирован.

    Этот клиент используется для выполнения внешних HTTP-запросов в API,
    таких как запросы к платформам Afterbuy или Mirakl.
    """
    if not resources.client:
        raise RuntimeError("Client not initialized")
    return resources.client

async def get_llm_agent():
    """
    Возвращает экземпляр LLM-агента для обработки запросов ИИ.
    Вызывает HTTPException с кодом 503, если агент не инициализирован.

    LLM-агент используется для задач, связанных с обработкой текста,
    генерацией ответов или анализом данных с помощью моделей ИИ.
    """
    if not resources.llm_agent:
        raise HTTPException(status_code=503, detail="LLM agent is not initialized")
    return resources.llm_agent

async def get_session():
    """
    Предоставляет асинхронную сессию базы данных для использования в зависимостях.
    Сессия автоматически закрывается после завершения запроса благодаря контекстному менеджеру.

    Эта зависимость используется в маршрутах для выполнения операций с базой данных,
    обеспечивая транзакционность и изоляцию запросов.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)):
    """
    Извлекает текущего аутентифицированного пользователя на основе JWT-токена.
    Проверяет токен, декодирует его и получает пользователя из базы данных.

    Параметры:
    - token: JWT-токен, полученный из заголовка Authorization
    - session: Асинхронная сессия базы данных

    Возвращает:
    - Объект пользователя, если токен валиден и пользователь найден

    Вызывает HTTPException:
    - 401, если токен истек или пользователь не найден
    """
    try:
        token_data = decode_access_token(token)  # Декодирование токена для получения данных
    except JWTError:
        raise HTTPException(status_code=401, detail="Token is expired")  # Токен недействителен
    user = await get_user_by_username(session=session, username=token_data.get("username"))  # Поиск пользователя
    if not user:
        raise HTTPException(status_code=401, detail="User not found")  # Пользователь не найден
    return user

async def require_admin_token(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)):
    """
    Проверяет, что токен принадлежит администратору и возвращает объект администратора.
    Используется для защиты маршрутов, требующих административных прав.

    Параметры:
    - token: JWT-токен администратора
    - session: Асинхронная сессия базы данных

    Возвращает:
    - Объект администратора, если токен валиден и пользователь имеет права админа

    Вызывает HTTPException:
    - 403, если пользователь не имеет достаточных прав или токен недействителен
    """
    data = decode_access_token(token)  # Декодирование токена
    if not data.get("is_admin"):  # Проверка флага администратора в токене
        raise HTTPException(status_code=403, detail="Not enough permissions")
    admin_user = await get_user_by_username(session=session, username=data.get("username"))  # Получение пользователя
    if not admin_user or not admin_user.is_admin:  # Дополнительная проверка в базе данных
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return admin_user
