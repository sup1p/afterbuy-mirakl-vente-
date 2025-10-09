from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    
class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None

class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str