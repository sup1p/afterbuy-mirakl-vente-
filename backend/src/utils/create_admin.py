import asyncio
from sqlalchemy import select
from src.models import User
from src.core.settings import settings
from src.core.dependencies import get_session
from src.core.security import get_password_hash


async def create_admin():
    """
    Асинхронная функция для создания администратора.
    Если администратор уже существует, проверяет его пароль и обновляет его при необходимости.
    Если администратора нет, создаёт нового.
    """
    # Получаем асинхронную сессию из генератора get_session()
    session_gen = get_session()
    session = await anext(session_gen)  # Берём первый yield из генератора

    try:
        # Проверяем, существует ли уже администратор с указанным именем пользователя
        result = await session.execute(select(User).where(User.username == settings.admin_username))
        admin = result.scalar_one_or_none()  # Получаем одного пользователя или None

        # Хэшируем пароль администратора
        hashed_pw = get_password_hash(settings.admin_password)

        if admin:
            # Если администратор уже существует
            if admin.hashed_password == hashed_pw:
                print("✅ Администратор уже существует")
                return
            else:
                # Если пароль отличается, обновляем его
                admin.hashed_password = hashed_pw
                await session.commit()
                print("🔄 Пароль администратора обновлён")
                return

        # Если администратора нет, создаём нового
        admin = User(
            username=settings.admin_username,
            hashed_password=hashed_pw,
            is_admin=True,  # Устанавливаем флаг администратора
        )
        session.add(admin)  # Добавляем нового пользователя в сессию
        await session.commit()  # Фиксируем изменения в базе данных
        print("🎉 Администратор создан")
    finally:
        # Закрываем генератор (чтобы сессия корректно закрылась)
        await session_gen.aclose()

if __name__ == "__main__":
    # Запускаем асинхронную функцию создания администратора
    asyncio.run(create_admin())
