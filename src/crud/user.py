from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import User
from src.core.security import get_password_hash

async def get_user_by_username(session: AsyncSession, username: str):
    q = select(User).where(User.username == username)
    res = await session.execute(q)
    return res.scalar_one_or_none()


async def create_user(session: AsyncSession, username: str, password: str) -> User:
    user = User(username=username, hashed_password=get_password_hash(password))
    session.add(user)
    await session.flush()  # чтобы получить id
    await session.refresh(user)
    return user
