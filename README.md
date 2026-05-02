# WispChat - Защищенный чат-сервер

Безопасный веб-чат с шифрованием сообщений, аутентификацией через JWT и поддержкой дружеских связей.

## 🔒 Особенности безопасности

- **Шифрование сообщений**: AES-256 (Fernet) для всех сообщений
- **JWT аутентификация**: Токены с ограниченным временем жизни
- **Хеширование паролей**: bcrypt с SHA-256 pre-hashing
- **Rate limiting**: Защита от DDoS и брутфорса
- **Валидация токенов в WebSocket**: Двойная проверка подлинности

## 🚀 Быстрый старт

### 1. Настройка окружения

```bash
# Скопируйте шаблон .env
cp .env.example .env

# Сгенерируйте безопасные ключи
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_hex(32))" >> .env
```

### 2. Запуск с Docker (рекомендуется)

#### Production режим:
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

#### Development режим (с hot-reload):
```bash
docker-compose -f docker-compose.dev.yml up --build
```

### 3. Запуск без Docker

```bash
# Установка зависимостей
pip install -r requirements.txt

# Применение миграций
python scripts/run_migrations.py

# Запуск сервера
python -m app.main
```

Приложение будет доступно по адресу: `http://localhost:8000`

## 📁 Структура проекта

```
wispchat/
├── app/
│   ├── core/           # Конфигурация, безопасность, WebSocket
│   ├── models/         # SQLAlchemy модели
│   ├── routers/        # API эндпоинты
│   ├── services/       # Бизнес-логика
│   ├── repositories/   # Работа с БД
│   └── schemas/        # Pydantic схемы
├── scripts/            # Утилиты (миграции и т.д.)
├── alembic/            # Миграции БД
├── templates/          # HTML шаблоны
├── static/             # Статические файлы
├── data/               # SQLite база данных (создается автоматически)
├── .env.example        # Шаблон переменных окружения
├── docker-compose.*.yml # Конфигурации Docker
└── README.md
```

## ⚙️ Конфигурация

### Переменные окружения (.env)

| Переменная | Описание | Пример |
|------------|----------|--------|
| `SECRET_KEY` | Ключ для JWT | `a1b2c3...` (64 hex) |
| `ENCRYPTION_KEY` | Ключ шифрования сообщений | `d4e5f6...` (64 hex) |
| `APP_ENV` | Окружение | `production` / `development` |
| `DEBUG` | Режим отладки | `true` / `false` |
| `PORT` | Порт сервера | `8000` |
| `DATABASE_URL` | URL базы данных | `sqlite+aiosqlite:///./data/wispchat.db` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена | `30` |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Лимит запросов | `60` |

## 🔧 API Endpoints

### Аутентификация
- `POST /register` - Регистрация пользователя
- `POST /login` - Вход и получение JWT токена

### Чат
- `GET /` - Главная страница чата
- `WS /ws?token=<JWT>` - WebSocket для обмена сообщениями

### Друзья
- `GET /friends` - Список друзей
- `POST /friends/add` - Запрос в друзья
- `POST /friends/accept` - Принять запрос
- `DELETE /friends/remove` - Удалить из друзей

## 🧪 Тестирование

```bash
# Запуск тестов
pytest

# Запуск с покрытием
pytest --cov=app
```

## 📊 База данных

Проект использует SQLite с Alembic для миграций.

```bash
# Применить все миграции
python scripts/run_migrations.py

# Создать новую миграцию
alembic revision --autogenerate -m "Description"

# Откатить последнюю миграцию
alembic downgrade -1
```

## 🐳 Docker

### Сборка образа
```bash
docker build -t wispchat .
```

### Запуск контейнера
```bash
docker run -d \
  -p 8000:8000 \
  -v wispchat_data:/app/data \
  -v $(pwd)/.env:/app/.env:ro \
  --name wispchat \
  wispchat
```

### Health check
```bash
curl http://localhost:8000/docs
```

## 🛡️ Безопасность

### Рекомендации для production

1. **Никогда не используйте ключи по умолчанию** - сгенерируйте уникальные ключи
2. **Используйте HTTPS** - настройте reverse proxy (nginx, traefik)
3. **Обновляйте зависимости** - регулярно проверяйте `pip audit`
4. **Настройте firewall** - откройте только необходимые порты
5. **Мониторьте логи** - отслеживайте подозрительную активность

## 📝 Лицензия

MIT License

## 🤝 Вклад в проект

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request
