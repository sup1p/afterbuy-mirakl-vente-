import asyncio
from sqlalchemy import select
from src.models import User
from src.core.settings import settings
from src.core.dependencies import get_session
from src.core.security import get_password_hash


async def create_admin():
    # получаем асинхронную сессию из get_session()
    session_gen = get_session()
    session = await anext(session_gen)   # берём первый yield

    try:
        # Проверяем, есть ли уже админ
        result = await session.execute(select(User).where(User.username == settings.admin_username))
        admin = result.scalar_one_or_none()

        if admin:
            print("✅ Admin already exists")
            return

        # Создаём нового админа
        hashed_pw = get_password_hash(settings.admin_password)
        admin = User(
            username=settings.admin_username,
            hashed_password=hashed_pw,
            is_admin=True,
        )
        session.add(admin)
        await session.commit()
        print("🎉 Admin user created")
    finally:
        # закрываем генератор (чтобы сессия корректно закрылась)
        await session_gen.aclose()


if __name__ == "__main__":
    asyncio.run(create_admin())
