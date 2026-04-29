from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db_session
from app.schemas import RegisterRequest, TokenResponse
from app.core import hash_password, verify_password, create_jwt, DUMMY_HASH
from app.rate_limiter import limiter
import re
from app.models import User, OfflineMessage, Friendship

router = APIRouter(tags=["Авторизация"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, req: RegisterRequest, session: AsyncSession = Depends(get_db_session)):
    if not re.match(r"^[a-zA-Z0-9_-]{3,32}$", req.username):
        raise HTTPException(status_code=400, detail="Имя пользователя: 3–32 символа, только латиница, цифры, '_' и '-'")
    
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Пароль: минимум 8 символов")
    if not re.search(r"[A-Za-z]", req.password) or not re.search(r"\d", req.password):
        raise HTTPException(status_code=400, detail="Пароль должен содержать как минимум одну букву и одну цифру")

    result = await session.execute(select(User).where(User.username == req.username))
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="Пользователь уже существует")

    new_user = User(username=req.username, password_hash=hash_password(req.password))
    session.add(new_user)
    await session.commit()
    
    token = create_jwt(req.username)
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(User).where(User.username == form.username))
    user = result.scalars().first()

    if not user:
        # Dummy хеширование для выравнивания времени ответа при неверном логине
        verify_password(form.password, DUMMY_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_jwt(form.username)
    return TokenResponse(access_token=token)