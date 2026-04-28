from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.database import db_conn
from app.schemas import RegisterRequest, TokenResponse
from app.security import hash_password, verify_password, create_jwt

# Создаем роутер с тегом для удобства в Swagger UI
router = APIRouter(tags=["Авторизация"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    if len(req.username) < 3 or len(req.username) > 32:
        raise HTTPException(status_code=400, detail="Имя пользователя: 3–32 символа")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Пароль: минимум 8 символов")

    cursor = db_conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE username = ?", (req.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Пользователь уже существует")

    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (req.username, hash_password(req.password))
    )
    db_conn.commit()
    token = create_jwt(req.username)
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    cursor = db_conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (form.username,))
    row = cursor.fetchone()

    if not row or not verify_password(form.password, row[0]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_jwt(form.username)
    return TokenResponse(access_token=token)