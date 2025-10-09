from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import User
from src.core.security import get_password_hash

async def get_user_by_username(session: AsyncSession, username: str):
    """
    Получает пользователя по имени пользователя.
    Используется для аутентификации и проверки существования пользователя.
    Возвращает объект User или None, если пользователь не найден.
    """
    q = select(User).where(User.username == username)
    res = await session.execute(q)
    return res.scalar_one_or_none()

async def get_user_by_id(session: AsyncSession, user_id: int):
    """
    Получает пользователя по ID.
    Используется для получения данных пользователя по его идентификатору.
    Возвращает объект User или None, если пользователь не найден.
    """
    q = select(User).where(User.id == user_id)
    res = await session.execute(q)
    return res.scalar_one_or_none()

async def get_users(session: AsyncSession):
    """
    Получает всех пользователей системы.
    Используется для административных целей, например, для управления пользователями.
    Возвращает список всех объектов User.
    """
    q = select(User)
    res = await session.execute(q)
    return res.scalars().all()

async def create_user(session: AsyncSession, username: str, password: str) -> User:
    """
    Создает нового пользователя с заданным именем и паролем.
    Пароль автоматически хэшируется перед сохранением.
    Возвращает созданный объект User с присвоенным ID.
    """
    user = User(username=username, hashed_password=get_password_hash(password))
    session.add(user)
    await session.flush()  # чтобы получить id
    await session.refresh(user)
    return user
