import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.rate_limiter import limiter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import engine
from app.routers import auth, chat, friends

# Современный метод управления жизненным циклом приложения FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Логика, выполняемая при ЗАПУСКЕ сервера
    yield # Сервер работает
    # Логика, выполняемая при ОСТАНОВКЕ сервера
    await engine.dispose()

app = FastAPI(title="Защищенный Чат-Сервер", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    from fastapi.responses import Response
    return Response(status_code=204)

app.include_router(auth.router)
app.include_router(friends.router)
app.include_router(chat.router)

if __name__ == "__main__":
    # Выполняем миграции БД до запуска Uvicorn (пока Event Loop не создан)
    import logging
    from alembic.config import Config
    from alembic import command
    
    logging.info("Running database migrations...")
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logging.info("Database migrations completed.")
    except Exception as e:
        logging.error(f"Failed to run migrations: {e}")
        # Для случаев, когда alembic.ini не найден или БД недоступна
        pass

    # Запускаем Uvicorn на хосте и порту из конфигурации
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)