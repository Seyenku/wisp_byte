from fastapi import FastAPI
import uvicorn

from app.database import init_db
from app.routers import auth, chat, friends

# Инициализируем БД при старте
init_db()

app = FastAPI(title="Защищенный Чат-Сервер")

# Подключаем наши роутеры
app.include_router(auth.router)
app.include_router(friends.router)
app.include_router(chat.router)

if __name__ == "__main__":
    # Обратите внимание: путь "app.main:app" важен для корректной работы
    uvicorn.run("app.main:app", host="0.0.0.0", port=12251)