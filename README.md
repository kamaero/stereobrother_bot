# StereoBrother Bot - ИИ-обработка и реставрация аудио

![StereoBrother Logo](https://via.placeholder.com/800x200/4F46E5/FFFFFF?text=StereoBrother+Audio+AI+Bot)

Бот для автоматической обработки, улучшения и мастеринга аудиофайлов с использованием искусственного интеллекта. Основной акцент делается на восстановлении старых/некачественных записей (диктофоны, аудиокассеты) и студийной обработке.

## 🚀 Возможности

### 🎵 Улучшение качества (Restoration Enhancement)
- **Улучшение полного микса** - комплексное улучшение звучания всей композиции
- **Улучшение отдельных дорожек** - специализированные алгоритмы для конкретных инструментов:
  - Ударные (Drums)
  - Гитары (Guitars)
  - Бас (Bass)
  - Струнные (Strings)
  - Пианино/Клавишные (Piano)
  - Голос/Вокал (Vocals)

### 🔇 Чистка звука (Denoise)
- Удаление треска, шипения (hiss), технического/фонового шума оборудования
- Интеллектуальное подавление шумов с сохранением полезного сигнала

### 🎛️ Разделение на дорожки (Stem Separation)
- Разложение готового трека на отдельные инструменты (мультитрек)
- Разделение на 4–6 дорожек (Вокал, Бас, Ударные, Мелодия/Другое)
- Качество как на сайте uvronline.app

### 🎚️ ИИ-Мастеринг (AI Mastering)
- Автоматическая финальная обработка трека на основе готовых шаблонов АЧХ
- Пресеты одной кнопкой:
  - **Мастеринг подкаста** - акцент на четкость речи
  - **Мастеринг песни** - музыкальный баланс, плотность
  - **Мастеринг рекламы** - громкость, яркость, "радийный" звук

## 📊 Монетизация

- **Модель распространения**: Ежемесячная подписка
- **Стоимость**: До 500 рублей в месяц
- **Дневной лимит**: До 100 генераций в сутки на одного пользователя
- **Лимит длительности**: Обработка файлов длиной до 10 минут

## 🛠️ Технические требования

### Входные форматы
- MP3, WAV, M4A, OGG, FLAC, AAC, WMA

### Выходные форматы
- WAV (без сжатия)
- MP3 (сжатый формат)

## 🏗️ Архитектура

### Технологический стек
- **Backend**: Python (FastAPI)
- **AI/ML**: PyTorch/TensorFlow, Demucs, Spleeter
- **База данных**: PostgreSQL
- **Кеширование**: Redis
- **Хранилище файлов**: S3/MinIO
- **Очереди задач**: Celery + Redis

### Модели ИИ
- **Денойзинг**: Demucs, Spleeter
- **Разделение дорожек**: Demucs, Spleeter, Open-Unmix
- **Улучшение качества**: AudioSuperResolution, SEANet
- **Мастеринг**: Нейросетевые модели на основе анализа эталонных треков

## 🚀 Быстрый старт

### Предварительные требования
- Docker и Docker Compose
- Python 3.11+
- FFmpeg

### Установка с Docker (рекомендуется)

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/stereobrother_bot.git
cd stereobrother_bot
```

2. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл под свои нужды
```

3. Запустите приложение:
```bash
docker-compose up -d
```

4. Приложение будет доступно по адресу:
- API: http://localhost:8000
- Документация API: http://localhost:8000/docs
- MinIO: http://localhost:9001
- Grafana: http://localhost:3000
- pgAdmin: http://localhost:5050

### Установка без Docker

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Установите системные зависимости:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg libsndfile1

# macOS
brew install ffmpeg libsndfile
```

3. Настройте базу данных:
```bash
# Создайте базу данных PostgreSQL
createdb stereobrother_db

# Или используйте SQLite для разработки
```

4. Запустите приложение:
```bash
uvicorn src.main:app --reload
```

## 📚 API Документация

После запуска приложения документация API доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Основные эндпоинты

#### Аутентификация
- `POST /api/auth/register` - Регистрация пользователя
- `POST /api/auth/login` - Вход в систему
- `POST /api/auth/refresh` - Обновление токена

#### Обработка аудио
- `POST /api/audio/upload` - Загрузка аудиофайла
- `POST /api/audio/enhance` - Улучшение качества
- `POST /api/audio/denoise` - Очистка от шумов
- `POST /api/audio/separate` - Разделение на дорожки
- `POST /api/audio/master` - Мастеринг
- `GET /api/audio/task/{task_id}` - Статус задачи
- `GET /api/audio/history` - История обработок

#### Пользователь
- `GET /api/user/profile` - Профиль пользователя
- `GET /api/user/usage` - Информация об использовании

#### Подписка
- `POST /api/subscription/create` - Создание подписки
- `GET /api/subscription/status` - Статус подписки

## 🔧 Конфигурация

Основные настройки находятся в файле `config/settings.py`. Для окружения можно использовать переменные окружения или файл `.env`.

### Основные настройки
```python
# Настройки лимитов
MAX_FILE_DURATION_MINUTES = 10  # Максимальная длительность файла
DAILY_GENERATION_LIMIT = 100    # Дневной лимит генераций
SUBSCRIPTION_PRICE_RUB = 500    # Стоимость подписки

# Настройки обработки
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHANNELS = 2
AUDIO_BIT_DEPTH = 16
```

## 🧪 Тестирование

### Запуск тестов
```bash
# Все тесты
pytest

# С покрытием кода
pytest --cov=src --cov-report=html

# Конкретный тест
pytest tests/test_audio_processor.py -v
```

### Тестовые данные
Тестовые аудиофайлы находятся в директории `tests/fixtures/audio/`.

## 📊 Мониторинг

### Метрики Prometheus
- Доступны по адресу: http://localhost:9090
- Эндпоинт метрик: http://localhost:8000/metrics

### Графический интерфейс Grafana
- Доступен по адресу: http://localhost:3000
- Логин: admin, Пароль: admin

### Мониторинг Celery
- Flower доступен по адресу: http://localhost:5555

## 🔒 Безопасность

### Защита от злоупотреблений
- Rate limiting по IP и пользователю
- Проверка форматов и размеров файлов
- Анализ контента на предмет запрещенного материала

### Конфиденциальность
- Шифрование файлов при передаче и хранении
- Автоматическое удаление временных файлов
- Политика хранения обработанных файлов (30 дней по умолчанию)

## 📈 Масштабирование

### Горизонтальное масштабирование
```bash
# Увеличение количества воркеров
docker-compose up --scale worker=4 -d

# Увеличение количества инстансов API
docker-compose up --scale api=3 -d
```

### Мониторинг нагрузки
- Используйте Grafana для мониторинга метрик
- Настройте алерты в Prometheus

## 🤝 Вклад в проект

### Установка для разработки
```bash
# Клонируйте репозиторий
git clone https://github.com/yourusername/stereobrother_bot.git
cd stereobrother_bot

# Установите зависимости для разработки
pip install -r requirements-dev.txt

# Установите pre-commit хуки
pre-commit install

# Запустите тесты
pytest
```

### Правила коммитов
- Используйте Conventional Commits
- Пишите осмысленные сообщения коммитов
- Добавляйте тесты для нового функционала

### Code Style
- Black для форматирования
- isort для сортировки импортов
- flake8 для проверки стиля
- mypy для проверки типов

## 📄 Лицензия

Этот проект лицензирован под лицензией MIT. Смотрите файл [LICENSE](LICENSE) для подробностей.

## 📞 Поддержка

- **Документация**: [docs.stereobrother.com](https://docs.stereobrother.com)
- **Техническая поддержка**: support@stereobrother.com
- **Сообщество**: [Telegram канал](https://t.me/stereobrother)
- **Issues**: [GitHub Issues](https://github.com/yourusername/stereobrother_bot/issues)

## 🙏 Благодарности

- [Demucs](https://github.com/facebookresearch/demucs) - для разделения дорожек
- [Spleeter](https://github.com/deezer/spleeter) - для разделения дорожек
- [Librosa](https://librosa.org/) - для обработки аудио
- [FastAPI](https://fastapi.tiangolo.com/) - для API фреймворка

---

**StereoBrother Bot** - сделайте ваше аудио идеальным с помощью искусственного интеллекта! 🎧✨