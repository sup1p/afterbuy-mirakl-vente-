import os
from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import jwt, JWTError
from pydantic import BaseModel
from src.core.settings import settings


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие открытого пароля его хэшированной версии.
    Используется для аутентификации пользователей при входе в систему.
    Возвращает True, если пароль верный, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Генерирует хэш для открытого пароля с использованием bcrypt.
    Хэш сохраняется в базе данных для безопасного хранения паролей.
    Возвращает строку с хэшированным паролем.
    """
    return pwd_context.hash(password)

def create_access_token(subject: str, is_admin: bool, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает JWT access-токен для аутентификации пользователя.
    Токен содержит информацию о пользователе (subject) и его правах администратора.
    Если expires_delta не указан, используется значение по умолчанию из настроек.
    Возвращает закодированный JWT-токен в виде строки.
    """
    to_encode = {"sub": subject, "is_admin": is_admin}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: str, is_admin: bool, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает JWT refresh-токен для обновления access-токенов.
    Refresh-токен имеет более длительный срок действия и используется для получения новых access-токенов.
    Если expires_delta не указан, используется значение по умолчанию (дни из настроек).
    Возвращает закодированный JWT-токен в виде строки.
    """
    to_encode = {"sub": subject, "is_admin": is_admin}
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.refresh_token_expire_days))
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_and_generate_access_from_refresh(refresh_token: str) -> str:
    """
    Проверяет refresh-токен и генерирует новый access-токен на его основе.
    Используется для обновления сессии пользователя без повторного входа.
    Если токен недействителен или не является refresh-токеном, вызывает исключение.
    Возвращает новый access-токен.
    """
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise JWTError("Token is not a refresh token")
        username = payload.get("sub")
        is_admin = payload.get("is_admin", False)
        if not username:
            raise JWTError("Missing subject in token")
        return create_access_token(subject=username, is_admin=is_admin)
    except JWTError as e:
        raise e

def decode_access_token(token: str):
    """
    Декодирует и проверяет access-токен, извлекая информацию о пользователе.
    Используется для аутентификации запросов в зависимостях FastAPI.
    Если токен недействителен, вызывает исключение.
    Возвращает словарь с username и флагом is_admin.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise JWTError("Missing subject in token")
        return {
            "username": username,
            "is_admin": payload.get("is_admin", False)
        }
    except JWTError as e:
        raise e
