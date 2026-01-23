# Dockerfile для бота обработки аудио StereoBrother

# Используем официальный Python образ
FROM python:3.11-slim AS builder

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаем финальный образ
FROM python:3.11-slim AS runtime

# Устанавливаем системные зависимости для runtime
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Настраиваем рабочую директорию
WORKDIR /app

# Копируем установленные зависимости из builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

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
