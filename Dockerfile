# Dockerfile для бота обработки аудио StereoBrother

# Используем официальный Python образ
FROM python:3.11-slim as builder

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    ffmpeg \
    libsndfile1 \
    libsndfile-dev \
    libavcodec-extra \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry для управления зависимостями
RUN pip install poetry==1.7.0

# Настраиваем Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock* ./

# Устанавливаем зависимости
RUN poetry install --no-root --only main

# Создаем финальный образ
FROM python:3.11-slim as runtime

# Устанавливаем системные зависимости для runtime
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libavcodec-extra \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Настраиваем рабочую директорию
WORKDIR /app

# Копируем виртуальное окружение из builder
COPY --from=builder /app/.venv .venv
ENV PATH="/app/.venv/bin:$PATH"

# Копируем исходный код
COPY . .

# Создаем необходимые директории
RUN mkdir -p \
    /app/storage \
    /app/temp \
    /app/logs \
    /app/models \
    && chown -R appuser:appuser /app

# Переключаемся на непривилегированного пользователя
USER appuser

# Экспортируем переменные окружения
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    TZ=Europe/Moscow

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
