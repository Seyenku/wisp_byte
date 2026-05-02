# Техническое задание на рефакторинг проекта WispChat

## 📋 Общая информация

**Проект:** WispChat — защищённый мессенджер с шифрованием сообщений  
**Целевая среда:** Docker-контейнер на базе `python:3.11-slim` (VPS, production)  
**База данных:** SQLite + aiosqlite (внутри контейнера)  
**Фреймворк:** FastAPI + WebSocket  

---

## 🎯 Цели рефакторинга

1. **Безопасность** — устранить критические уязвимости
2. **Стабильность** — улучшить обработку ошибок и жизненный цикл приложения
3. **Производительность** — оптимизировать работу с БД и WebSocket
4. **Поддерживаемость** — устранить циркулярные импорты, улучшить структуру кода
5. **Документирование** — добавить API-документацию и инструкции

---

## 🔒 1. Безопасность (Критический приоритет)

### 1.1. Исправление генерации ключей шифрования

**Проблема:** В файле `/app/core/config.py` ключи генерируются заново при каждом запуске, если не указаны в `.env`:
```python
secret_key: str = secrets.token_hex(32)  # ❌ Генерируется каждый запуск
msg_encryption_key: str = Fernet.generate_key().decode()  # ❌ Генерируется каждый запуск
```

**Требуется:**
- [ ] Изменить конфигурацию так, чтобы приложение **требовало** наличия ключей в `.env` или переменных окружения
- [ ] При отсутствии ключей — выбрасывать исключение на старте приложения
- [ ] Добавить проверку формата ключей (валидация)

**Реализация:**
```python
# app/core/config.py
from pydantic import Field, field_validator
import base64

class Settings(BaseSettings):
    secret_key: str = Field(..., min_length=32)
    msg_encryption_key: str = Field(...)
    
    @field_validator('msg_encryption_key')
    @classmethod
    def validate_fernet_key(cls, v):
        try:
            key = v.encode() if isinstance(v, str) else v
            base64.urlsafe_b64decode(key)
            return v
        except Exception:
            raise ValueError('Некорректный ключ Fernet (должен быть base64-encoded 32 байта)')
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
```

### 1.2. Улучшение валидации токена в WebSocket

**Проблема:** Токен передаётся как query-параметр `ws?token=...`, что менее безопасно.

**Требуется:**
- [ ] Добавить поддержку передачи токена через WebSocket subprotocol или заголовок
- [ ] Сохранить обратную совместимость с query-параметром
- [ ] Добавить логирование попыток несанкционированного доступа

**Реализация:**
```python
# app/routers/router_chat.py
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Попытка получить токен из разных источников
    token = (
        websocket.query_params.get("token") or
        websocket.headers.get("authorization", "").replace("Bearer ", "") or
        websocket.subprotocols[0] if websocket.subprotocols else None
    )
    
    if not token:
        await websocket.close(code=4401, reason="Token required")
        return
    
    username = decode_jwt(token)
    if not username:
        await websocket.close(code=4401, reason="Invalid token")
        return
    # ... остальная логика
```

### 1.3. Rate limiting для WebSocket

**Проблема:** На WebSocket-соединения не распространяется rate limiting.

**Требуется:**
- [ ] Добавить ограничение на количество сообщений в минуту от одного пользователя
- [ ] Добавить глобальное ограничение на количество одновременных WebSocket-соединений
- [ ] При превышении лимита — закрывать соединение с кодом 4429 (Too Many Requests)

---

## 🏗️ 2. Архитектура и структура кода (Высокий приоритет)

### 2.1. Устранение циркулярных импортов

**Проблема:** В файлах наблюдаются циркулярные импорты:
- `app/core/websocket.py` импортирует модели в конце файла
- `app/services/service_friend.py` импортирует `manager` внутри метода

**Требуется:**
- [ ] Переместить все импорты в начало файлов
- [ ] Использовать `TYPE_CHECKING` для типов, используемых только в аннотациях
- [ ] При необходимости использовать строковые аннотации типов (`"ConnectionManager"`)

**Реализация:**
```python
# app/core/websocket.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import Friendship, OfflineMessage, User

# Удалить импорт в конце файла
# from sqlalchemy import select, and_, or_  <- переместить вверх
```

### 2.2. Исправление работы с путями

**Проблема:** В `main.py` используется `sys.path.append()` перед импортами для корректной работы в Docker.

**Требуется:**
- [ ] Сохранить текущее решение (оно рабочее для Docker)
- [ ] Добавить комментарий о причине такого расположения
- [ ] Использовать `BASE_DIR` во всех местах работы с файлами

**Реализация:**
```python
# app/main.py
import os
import sys

# Требуется для корректной работы импортов в Docker-контейнере
# Не перемещать после импортов!
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Использовать BASE_DIR вместо повторных вычислений
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
```

### 2.3. Удаление или интеграция UserService

**Проблема:** `UserService` существует, но не используется в роутерах.

**Требуется:**
- [ ] **Вариант A (рекомендуемый):** Начать использовать `UserService` в `router_auth.py` для проверки существования пользователя
- [ ] **Вариант B:** Удалить `UserService` и `get_user_service`, если функциональность дублируется

**Реализация (Вариант A):**
```python
# app/routers/router_auth.py
from app.dependencies import get_user_service

@router.post("/login", ...)
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),  # Добавить
):
    # Можно добавить дополнительную логику с user_service
    token = await auth_service.login(form.username, form.password)
    return TokenResponse(access_token=token)
```

### 2.4. Централизованная обработка исключений

**Требуется:**
- [ ] Добавить глобальный обработчик исключений для WebSocket
- [ ] Логировать все исключения с контекстом (username, action)
- [ ] Не раскрывать детали ошибок клиенту

```python
# app/core/websocket.py
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    async def connect(self, websocket: WebSocket, username: str):
        try:
            await websocket.accept()
            self.active_connections[username] = websocket
            # ...
        except Exception as e:
            logger.error(f"Error connecting user {username}: {e}", exc_info=True)
            if not websocket.client_state.DISCONNECTED:
                await websocket.close(code=4000, reason="Internal error")
            raise
```

---

## 📊 3. База данных (Средний приоритет)

### 3.1. Добавление индексов

**Проблема:** Отсутствуют индексы на часто используемых полях.

**Требуется:**
- [ ] Добавить составной индекс на `(receiver, id)` для `offline_messages` (быстрая выборка непрочитанных)
- [ ] Добавить индекс на `status` в таблице `friendships` для фильтрации
- [ ] Создать новую миграцию Alembic

**Реализация:**
```python
# alembic/versions/003_add_indexes.py
def upgrade() -> None:
    op.create_index(
        'ix_offline_messages_receiver_id',
        'offline_messages',
        ['receiver', 'id']
    )
    op.create_index(
        'ix_friendships_status',
        'friendships',
        ['status']
    )
```

### 3.2. Ограничения длины строковых полей

**Проблема:** Поля `ciphertext`, `password_hash` не имеют ограничения длины.

**Требуется:**
- [ ] Добавить `String(length=...)` для всех текстовых полей
- [ ] Учесть, что зашифрованный текст длиннее оригинала (~33% overhead у Fernet)
- [ ] Создать миграцию для изменения существующих колонок

**Рекомендуемые размеры:**
- `ciphertext`: `String(8192)` (для сообщений до ~6KB)
- `password_hash`: `String(256)` (bcrypt + SHA256)

### 3.3. Вынос миграций из main.py

**Проблема:** Миграции выполняются внутри `main.py` при запуске через `uvicorn.run()`.

**Требуется:**
- [ ] Создать отдельный скрипт `scripts/run_migrations.py`
- [ ] Обновить `Dockerfile` для выполнения миграций перед запуском приложения
- [ ] Добавить обработку ошибок миграций с откатом

**Реализация:**
```python
# scripts/run_migrations.py
#!/usr/bin/env python3
import logging
import sys
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    alembic_cfg = Config("alembic.ini")
    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Миграции успешно выполнены")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка миграций: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
```

```dockerfile
# Dockerfile
# ... после установки зависимостей
COPY scripts/run_migrations.py .
RUN python run_migrations.py || exit 1

CMD ["python", "-m", "app.main"]
```

---

## 🚀 4. Производительность (Средний приоритет)

### 4.1. Оптимизация проверки онлайн-статуса друзей

**Проблема:** При большом количестве друзей проверка `f in manager.active_connections` выполняется линейно.

**Требуется:**
- [ ] Использовать `set` для `active_connections.keys()` при множественных проверках
- [ ] Кэшировать список друзей на время жизни запроса

**Реализация:**
```python
# app/services/service_friend.py
async def get_friends_list(self, username: str) -> List[Dict[str, Any]]:
    from app.core.websocket import manager
    
    friends = await self.friendship_repo.get_friends_list(username)
    online_users = set(manager.active_connections.keys())  # Один раз создаём set
    
    return [
        {"username": f, "online": f in online_users}
        for f in friends
    ]
```

### 4.2. Пагинация для offline messages

**Проблема:** При большом количестве накопленных сообщений загрузка всех сразу может быть медленной.

**Требуется:**
- [ ] Добавить лимит на количество загружаемых offline-сообщений (например, 100 последних)
- [ ] Сортировать по `id DESC` для загрузки новейших

```python
# app/core/websocket.py
from sqlalchemy import desc

result = await session.execute(
    select(OfflineMessage)
    .where(OfflineMessage.receiver == username)
    .order_by(desc(OfflineMessage.id))
    .limit(100)
)
```

---

## 🧪 5. Тестирование (Желательный приоритет)

### 5.1. Модульные тесты

**Требуется:**
- [ ] Добавить pytest-тесты для сервисов (`service_auth`, `service_friend`, `service_message`)
- [ ] Добавить тесты для репозиториев с использованием тестовой БД
- [ ] Покрыть тестами валидацию токенов и паролей

**Структура:**
```
tests/
├── __init__.py
├── conftest.py              # Фикстуры (test_db, client, etc.)
├── test_auth.py             # Тесты регистрации и логина
├── test_friends.py          # Тесты дружбы
├── test_messages.py         # Тесты сообщений
├── test_websocket.py        # Тесты WebSocket
└── test_security.py         # Тесты шифрования и JWT
```

### 5.2. Интеграционные тесты

**Требуется:**
- [ ] Добавить тесты API endpoints с использованием `TestClient`
- [ ] Тестировать полный сценарий: регистрация → добавление друга → отправка сообщения

---

## 📝 6. Документация (Желательный приоритет)

### 6.1. OpenAPI спецификация

**Требуется:**
- [ ] Настроить автоматическую генерацию OpenAPI через FastAPI (`/openapi.json`)
- [ ] Добавить описания ко всем endpoint'ам (`summary`, `description`, `responses`)
- [ ] Добавить примеры запросов/ответов

```python
# app/main.py
app = FastAPI(
    title="WispChat API",
    description="Защищённый мессенджер с end-to-end шифрованием",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)
```

### 6.2. README.md

**Требуется создать файл `/workspace/README.md` со структурой:**

```markdown
# WispChat

Защищённый мессенджер с шифрованием сообщений.

## Возможности

- ✅ Регистрация и аутентификация через JWT
- ✅ Друзья и система заявок
- ✅ Real-time чат через WebSocket
- ✅ Шифрование сообщений (Fernet)
- ✅ Offline-сообщения
- ✅ Статусы онлайн/офлайн

## Быстрый старт

### Разработка (локально)

1. Клонируйте репозиторий
2. Создайте `.env` по образцу `.env.example`
3. Запустите Docker Compose:
   ```bash
   docker-compose up --build
   ```
4. Откройте http://localhost:12251/api/docs

### Production (VPS)

1. Сгенерируйте ключи:
   ```bash
   SECRET_KEY=$(openssl rand -hex 32)
   MSG_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
   ```
2. Создайте `.env` с ключами
3. Запустите контейнер:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Конфигурация

| Переменная | Описание | Пример |
|------------|----------|--------|
| `SECRET_KEY` | Ключ для JWT | `1c8c9073...` |
| `MSG_ENCRYPTION_KEY` | Ключ шифрования сообщений | `XQ8UyOlK...` |
| `PORT` | Порт сервера | `12251` |
| `HOST` | Хост для binding | `0.0.0.0` |

## API Documentation

- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`
- OpenAPI JSON: `/openapi.json`

## Структура проекта

[Описание структуры файлов]

## Лицензия

MIT
```

### 6.3. .env.example

**Требуется создать шаблон:**
```bash
# .env.example
SECRET_KEY=your-secret-key-here-32-chars-minimum
MSG_ENCRYPTION_KEY=your-fernet-key-here-base64-encoded
ACCESS_TOKEN_EXPIRE_MINUTES=15
PORT=12251
HOST=0.0.0.0
```

---

## 🐳 7. Docker (Учитывая ваши ограничения)

### 7.1. Оптимизация Dockerfile

**Текущий статус:** Используется `python:3.10-slim`, требуется обновление до `3.11-slim`.

**Требуется:**
- [ ] Обновить базовый образ до `python:3.11-slim`
- [ ] Добавить `.dockerignore` для исключения лишних файлов
- [ ] Добавить healthcheck
- [ ] Оптимизировать слои кэширования

**Реализация:**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости (кэшируется)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Выполняем миграции
RUN python -m alembic upgrade head

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:12251/api/docs')" || exit 1

EXPOSE 12251

CMD ["python", "-m", "app.main"]
```

```dockerignore
# .dockerignore
.git
.gitignore
__pycache__
*.pyc
*.pyo
*.db
.env
.venv
venv
*.md
.pytest_cache
.coverage
htmlcov
```

### 7.2. docker-compose.prod.yml

**Требуется создать отдельный файл для production:**

```yaml
# docker-compose.prod.yml
services:
  chat-app:
    build: .
    container_name: wispchat-prod
    ports:
      - "12251:12251"
    volumes:
      - chat-data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:12251/')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

volumes:
  chat-data:
```

---

## 📅 План работ

### Этап 1: Критические исправления (1-2 дня)
- [ ] 1.1. Исправление генерации ключей шифрования
- [ ] 1.2. Валидация токена в WebSocket
- [ ] 2.1. Устранение циркулярных импортов

### Этап 2: Стабилизация (2-3 дня)
- [ ] 1.3. Rate limiting для WebSocket
- [ ] 2.4. Централизованная обработка исключений
- [ ] 3.3. Вынос миграций из main.py
- [ ] 7.1. Оптимизация Dockerfile

### Этап 3: Оптимизация (2-3 дня)
- [ ] 3.1. Добавление индексов БД
- [ ] 3.2. Ограничения длины полей
- [ ] 4.1. Оптимизация проверки онлайн-статуса
- [ ] 4.2. Пагинация offline messages

### Этап 4: Документирование и тесты (3-4 дня)
- [ ] 5.1. Модульные тесты
- [ ] 5.2. Интеграционные тесты
- [ ] 6.1. OpenAPI спецификация
- [ ] 6.2. README.md
- [ ] 6.3. .env.example

**Общая оценка:** 8-12 рабочих дней

---

## ✅ Критерии приёмки

1. **Безопасность:**
   - Приложение не запускается без корректных ключей в `.env`
   - WebSocket принимает токены из заголовков/subprotocol
   - Rate limiting работает на всех endpoint'ах

2. **Код:**
   - Нет циркулярных импортов (проверка через `pylint` или аналог)
   - Все пути используют `BASE_DIR`
   - Обработка исключений логгируется

3. **База данных:**
   - Все таблицы имеют индексы на часто используемых полях
   - Строковые поля имеют ограничения длины
   - Миграции выполняются отдельно от запуска приложения

4. **Docker:**
   - Образ собирается без ошибок
   - Healthcheck проходит
   - `.dockerignore` исключает лишние файлы

5. **Документация:**
   - README.md содержит инструкции по запуску
   - OpenAPI спецификация доступна по `/api/docs`
   - Все endpoint'ы документированы

---

## 📎 Приложения

### A. Список файлов для изменения

| Файл | Изменения |
|------|-----------|
| `app/core/config.py` | Валидация ключей, обязательные поля |
| `app/core/websocket.py` | Обработка ошибок, пагинация, импорты |
| `app/routers/router_chat.py` | Валидация токена из разных источников |
| `app/main.py` | Использование `BASE_DIR`, комментарии |
| `app/services/service_friend.py` | Оптимизация проверки онлайн |
| `app/models/*.py` | Ограничения длины полей |
| `alembic/versions/` | Новые миграции для индексов |
| `Dockerfile` | Обновление образа, healthcheck |
| `.dockerignore` | Новый файл |
| `docker-compose.prod.yml` | Новый файл |
| `scripts/run_migrations.py` | Новый файл |
| `README.md` | Новый файл |
| `.env.example` | Новый файл |
| `tests/` | Новая директория с тестами |

### B. Команды для генерации ключей

```bash
# SECRET_KEY (минимум 32 символа)
openssl rand -hex 32

# MSG_ENCRYPTION_KEY (Fernet key, base64)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Проверка ключа Fernet
python -c "from cryptography.fernet import Fernet; Fernet('YOUR_KEY_HERE')"
```

### C. Полезные ссылки

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Migrations](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [SlowAPI Rate Limiting](https://github.com/laurentS/slowapi)
- [WebSockets in FastAPI](https://fastapi.tiangolo.com/advanced/websockets/)

---

**Дата составления:** 2026-01-XX  
**Версия ТЗ:** 1.0  
**Статус:** На согласовании
