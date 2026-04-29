from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db_session
from app.schemas import RegisterRequest, TokenResponse
from app.core.rate_limiter import limiter
from app.dependencies import get_auth_service
from app.services.auth import AuthService


router = APIRouter(tags=["Авторизация"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    req: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user and return JWT token."""
    token = await auth_service.register(req.username, req.password)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate user and return JWT token."""
    token = await auth_service.login(form.username, form.password)
    return TokenResponse(access_token=token)