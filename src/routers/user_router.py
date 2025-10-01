from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from src.crud import user
from src.schemas.user_schemas import RefreshTokenRequest, UserCreate, Token, UserOut, UserUpdate
from src.core.dependencies import get_current_user, get_session, require_admin_token
from src.crud.user import get_user_by_username, create_user, get_user_by_id, get_users
from src.core.security import create_refresh_token, verify_and_generate_access_from_refresh, verify_password, create_access_token

router = APIRouter()

@router.post("/auth/create-user", response_model=UserOut, status_code=201, tags=["user"])
async def create_user_endpoint(user_in: UserCreate, session: AsyncSession = Depends(get_session), current_user = Depends(require_admin_token)):
    existing = await get_user_by_username(session=session, username=user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="username already registered")
    user = await create_user(session, user_in.username, user_in.password)
    await session.commit()
    return user

@router.post("/auth/login", response_model=Token, tags=["user"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    # form_data: expect { "username": "...", "password": "..." }
    user = await get_user_by_username(session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(subject=user.username, is_admin=user.is_admin, expires_delta=timedelta(minutes=60))
    refresh_token = create_refresh_token(subject=user.username, is_admin=user.is_admin)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/auth/me", response_model=UserOut, tags=["user"])
async def read_users_me(current_user = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_admin": current_user.is_admin
    }

@router.post("/auth/refresh", tags=["user"])
async def refresh_token(data: RefreshTokenRequest):
    if not data.refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token required")
    try:
        new_access_token = verify_and_generate_access_from_refresh(data.refresh_token)
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    
@router.delete("/user/delete-user/{id}", status_code=204, tags=["user"])
async def delete_user(id: int, session: AsyncSession = Depends(get_session), current_user = Depends(require_admin_token)):
    deleting_user = await get_user_by_id(session, user_id=id)
    
    if not deleting_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if deleting_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself")
    
    if deleting_user.is_admin:
        raise HTTPException(status_code=403, detail="Cannot delete admin user")
    
    await session.delete(deleting_user)
    await session.commit()

    return f"User with id {id} deleted successfully"

@router.patch("/user/update-user/{id}", response_model=UserOut, tags=["user"])
async def update_user(id: int, user_in: UserUpdate, session: AsyncSession = Depends(get_session), current_user = Depends(require_admin_token)):
    updating_user = await get_user_by_id(session, user_id=id)
    
    if not updating_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if updating_user.is_admin:
        raise HTTPException(status_code=403, detail="Cannot update admin user")
    
    if user_in.username:
        updating_user.username = user_in.username
    if user_in.password:
        updating_user.hashed_password = user.get_password_hash(user_in.password)

    session.add(updating_user)
    await session.commit()
    await session.refresh(updating_user)
    
    return updating_user

@router.get("/user/list-users", response_model=list[UserOut], tags=["user"])
async def list_users(session: AsyncSession = Depends(get_session), current_user = Depends(require_admin_token)):
    users = await get_users(session)
    return users

@router.get("/user/get-user/{id}", response_model=UserOut, tags=["user"])
async def get_user(id: int, session: AsyncSession = Depends(get_session), current_user = Depends(require_admin_token)):
    getting_user = await get_user_by_id(session, user_id=id)
    
    if not getting_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return getting_user