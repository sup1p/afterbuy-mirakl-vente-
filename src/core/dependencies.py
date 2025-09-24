"""
Dependency injection module for FastAPI.
Provides HTTP client instances for API endpoints.
"""
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from src import resources
from src.core.settings import settings
from src.core.security import decode_access_token
from src.crud.user import get_user_by_username
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import httpx
import aioftp

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

engine = create_async_engine(settings.database_url, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_httpx_client() -> httpx.AsyncClient:
    """
    Returns the global HTTP client instance.
    Raises RuntimeError if client is not initialized.
    """
    if not resources.client:
        raise RuntimeError("Client not initialized")
    return resources.client


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
        
    
async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)):
    from jose import JWTError
    try:
        token_data = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user = await get_user_by_username(session=session, username=token_data.get("username"))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

async def require_admin_token(token: str = Depends(oauth2_scheme)):
    data = decode_access_token(token)
    if not data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return data
