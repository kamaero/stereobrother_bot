# Установка StereoBrother Bot на Apple Silicon M2

Это руководство по установке и запуску StereoBrother Bot на компьютерах с процессором Apple Silicon M2.

## Системные требования

- macOS 12.0 (Monterey) или новее
- Apple Silicon M2
- Homebrew
- Python 3.9+
- PostgreSQL 15+
- Redis 7+
- FFmpeg
- 8GB RAM (минимум), 16GB рекомендуется
- 10GB свободного места на диске

## Шаг 1: Установка системных зависимостей

### 1.1 Установка Homebrew (если не установлен)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 1.2 Установка зависимостей через Homebrew

```bash
# Обновление Homebrew
brew update

# Установка Python 3.11
brew install python@3.11

# Установка PostgreSQL
brew install postgresql@15

# Установка Redis
brew install redis

# Установка FFmpeg
brew install ffmpeg

# Установка libsndfile для работы с аудио
brew install libsndfile

# Установка portaudio для аудио обработки
brew install portaudio
```

### 1.3 Запуск сервисов

```bash
# Запуск PostgreSQL
brew services start postgresql@15

# Запуск Redis
brew services start redis

# Проверка статуса
brew services list
```

## Шаг 2: Настройка проекта

### 2.1 Клонирование и переход в директорию

```bash
cd ~/stereobrother_bot
```

### 2.2 Создание виртуального окружения

```bash
# Создание виртуального окружения
python3.11 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Обновление pip
pip install --upgrade pip setuptools wheel
```

### 2.3 Установка Python зависимостей

```bash
# Установка базовых зависимостей
pip install -r requirements.txt

# Если возникают ошибки с NumPy/SciPy на M2:
pip install --no-cache-dir numpy scipy

# Установка PyTorch для Apple Silicon (MPS)
pip install torch torchvision torchaudio
```

## Шаг 3: Настройка базы данных

### 3.1 Создание базы данных PostgreSQL

```bash
# Подключение к PostgreSQL
psql postgres

# В psql выполните:
CREATE DATABASE stereobrother_db;
CREATE USER stereobrother WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE stereobrother_db TO stereobrother;
\q
```

### 3.2 Применение схемы базы данных

```bash
# Запуск SQL скрипта инициализации
psql -U stereobrother -d stereobrother_db -f db/init.sql
```

## Шаг 4: Настройка переменных окружения

### 4.1 Создание .env файла

```bash
# Копирование примера конфигурации
cp env.example .env

# Редактирование .env файла
nano .env
```

### 4.2 Минимальная конфигурация для .env

```env
# Окружение
ENVIRONMENT=development
DEBUG=true

# Сервер
HOST=0.0.0.0
PORT=8000
WORKERS=2

# База данных
DATABASE_URL=postgresql://stereobrother:your_secure_password@localhost:5432/stereobrother_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Безопасность (ВАЖНО: измените в продакшене!)
SECRET_KEY=your-super-secret-key-change-in-production

# Хранилище
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./storage

# Временные файлы
TEMP_DIR=./temp

# Логирование
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# AI модели
AI_MODELS_PATH=./models

# Лимиты
MAX_FILE_DURATION_MINUTES=10
DAILY_GENERATION_LIMIT=100
SUBSCRIPTION_PRICE_RUB=500
```

## Шаг 5: Создание необходимых директорий

```bash
# Создание директорий для хранения файлов
mkdir -p storage temp logs models

# Создание .gitkeep файлов
touch storage/.gitkeep temp/.gitkeep logs/.gitkeep models/.gitkeep

# Установка прав доступа
chmod 755 storage temp logs models
```

## Шаг 6: Инициализация базы данных

```bash
# Запуск миграций (если используется Alembic)
alembic upgrade head

# Или создание таблиц через Python
python3 -c "
from src.database import init_db
import asyncio
asyncio.run(init_db())
"
```

## Шаг 7: Загрузка AI моделей (опционально)

```bash
# Скачивание модели Demucs для разделения треков
python3 -c "
import demucs.pretrained
demucs.pretrained.get_model('htdemucs')
"

# Модели будут сохранены в ~/.cache/torch/hub/
```

## Шаг 8: Запуск приложения

### 8.1 Запуск API сервера

```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск FastAPI с uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 8.2 Запуск Celery Worker (в отдельном терминале)

```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск Celery worker
celery -A src.tasks.celery_app worker --loglevel=info --concurrency=2
```

### 8.3 Запуск Celery Beat (в отдельном терминале)

```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск Celery beat для периодических задач
celery -A src.tasks.celery_app beat --loglevel=info
```

### 8.4 Запуск Flower для мониторинга Celery (опционально)

```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск Flower
celery -A src.tasks.celery_app flower --port=5555
```

## Шаг 9: Проверка установки

### 9.1 Проверка API

```bash
# Проверка health endpoint
curl http://localhost:8000/health

# Должен вернуть:
# {"status":"healthy","version":"1.0.0","environment":"development"}
```

### 9.2 Проверка документации API

Откройте в браузере:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 9.3 Проверка Flower (если запущен)

Откройте в браузере:
- Flower: http://localhost:5555

## Шаг 10: Запуск тестов

```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск всех тестов
pytest -v

# Запуск тестов с покрытием
pytest --cov=src --cov-report=html

# Просмотр отчета о покрытии
open htmlcov/index.html
```

## Использование Docker (альтернативный метод)

### Запуск через Docker Compose

```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка сервисов
docker-compose down

# Остановка с удалением volumes
docker-compose down -v
```

## Оптимизация для Apple Silicon M2

### Использование MPS (Metal Performance Shaders)

PyTorch автоматически определит и использует MPS для ускорения на Apple Silicon:

```python
import torch

# Проверка доступности MPS
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Using MPS (Apple Silicon GPU)")
else:
    device = torch.device("cpu")
    print("Using CPU")
```

### Настройка производительности

```bash
# В .env файле настройте:
WORKERS=2  # Для M2 оптимально 2-4 воркера
CELERY_CONCURRENCY=2  # Количество одновременных задач
```

## Решение проблем

### Проблема: Ошибка при установке NumPy/SciPy

```bash
# Очистка кэша pip
pip cache purge

# Установка через Homebrew Python
brew install python@3.11
/opt/homebrew/bin/python3.11 -m pip install numpy scipy
```

### Проблема: PostgreSQL не запускается

```bash
# Проверка статуса
brew services list

# Перезапуск PostgreSQL
brew services restart postgresql@15

# Проверка логов
tail -f /opt/homebrew/var/log/postgres.log
```

### Проблема: Redis не подключается

```bash
# Проверка, запущен ли Redis
redis-cli ping
# Должно вернуть: PONG

# Перезапуск Redis
brew services restart redis
```

### Проблема: FFmpeg не найден

```bash
# Проверка установки FFmpeg
which ffmpeg

# Переустановка FFmpeg
brew reinstall ffmpeg
```

### Проблема: Ошибки с аудио библиотеками

```bash
# Установка дополнительных зависимостей
brew install libsndfile portaudio

# Переустановка Python пакетов
pip uninstall soundfile librosa
pip install --no-cache-dir soundfile librosa
```

## Полезные команды

### Управление базой данных

```bash
# Подключение к БД
psql -U stereobrother -d stereobrother_db

# Backup базы данных
pg_dump -U stereobrother stereobrother_db > backup.sql

# Восстановление базы данных
psql -U stereobrother stereobrother_db < backup.sql
```

### Управление виртуальным окружением

```bash
# Активация
source venv/bin/activate

# Деактивация
deactivate

# Обновление requirements.txt
pip freeze > requirements.txt
```

### Очистка временных файлов

```bash
# Очистка temp директории
rm -rf temp/*

# Очистка логов
rm -rf logs/*.log

# Очистка кэша Python
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## Производственное развертывание

Для продакшена рекомендуется:

1. Использовать Gunicorn вместо uvicorn напрямую
2. Настроить Nginx как reverse proxy
3. Использовать systemd для управления сервисами
4. Настроить SSL/TLS сертификаты
5. Использовать внешнюю БД (не локальную)
6. Настроить мониторинг (Prometheus + Grafana)
7. Настроить резервное копирование

См. DEPLOYMENT.md для подробностей.

## Дополнительные ресурсы

- Документация FastAPI: https://fastapi.tiangolo.com/
- Документация Celery: https://docs.celeryproject.org/
- Документация PyTorch MPS: https://pytorch.org/docs/stable/notes/mps.html
- Demucs: https://github.com/facebookresearch/demucs

## Поддержка

Если возникли проблемы:
1. Проверьте логи приложения в `logs/app.log`
2. Проверьте логи PostgreSQL и Redis
3. Убедитесь, что все сервисы запущены
4. Проверьте .env конфигурацию

## Лицензия

См. LICENSE файл в корне проекта.