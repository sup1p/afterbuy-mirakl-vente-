from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from src.schemas.user_schemas import UserCreate, Token, UserOut
from src.core.dependencies import get_session, require_admin_token
from src.crud.user import get_user_by_username, create_user
from src.core.security import verify_password, create_access_token
from src.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/create-user", response_model=UserOut, status_code=201)
async def create_user_endpoint(user_in: UserCreate, session: AsyncSession = Depends(get_session), current_user = Depends(require_admin_token)):
    existing = await get_user_by_username(session=session, username=user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="username already registered")
    user = await create_user(session, user_in.username, user_in.password)
    await session.commit()
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    # form_data: expect { "username": "...", "password": "..." }
    user = await get_user_by_username(session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(subject=user.username, is_admin=user.is_admin, expires_delta=timedelta(minutes=60))
    return {"access_token": access_token, "token_type": "bearer"}
