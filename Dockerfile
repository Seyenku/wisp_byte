# Используем официальный легковесный образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости (если нужны для сборки некоторых пакетов, например bcrypt или cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь исходный код проекта в контейнер
COPY . .

# Открываем порт, на котором работает приложение
EXPOSE 12251

# Команда для запуска приложения (uvicorn запускается внутри main.py, поэтому запускаем скрипт)
CMD ["python", "-m", "app.main"]
