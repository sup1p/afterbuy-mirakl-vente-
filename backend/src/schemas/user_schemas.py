from pydantic import BaseModel

# Схема для создания нового пользователя
class UserCreate(BaseModel):
    username: str  # Имя пользователя
    password: str  # Пароль пользователя
    
# Схема для обновления данных пользователя
class UserUpdate(BaseModel):
    username: str | None = None  # Новое имя пользователя (опционально)
    password: str | None = None   # Новый пароль (опционально)

# Схема для вывода данных пользователя
class UserOut(BaseModel):
    id: int  # ID пользователя
    username: str  # Имя пользователя
    is_admin: bool  # Флаг администратора

    class Config:
        from_attributes = True  # Позволяет создавать модель из атрибутов ORM

# Схема для токена доступа
class Token(BaseModel):
    access_token: str   # Токен доступа
    refresh_token: str  # Токен обновления
    token_type: str = "bearer"  # Тип токена

# Схема для запроса обновления токена
class RefreshTokenRequest(BaseModel):
    refresh_token: str  # Токен обновления