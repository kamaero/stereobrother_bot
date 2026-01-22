# StereoBrother Bot - Краткое руководство по запуску

## 🚀 Быстрый старт за 5 минут

### 1. Клонирование и настройка
```bash
# Клонируйте проект
git clone <ваш-репозиторий>
cd stereobrother_bot

# Настройте переменные окружения
cp env.example .env
# Отредактируйте .env файл (минимальные настройки ниже)
```

### 2. Минимальная конфигурация (.env)
```env
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-change-this
DATABASE_URL=postgresql://postgres:password@localhost:5432/stereobrother_db
REDIS_URL=redis://localhost:6379/0
```

### 3. Запуск с Docker (рекомендуется)
```bash
# Запустите скрипт быстрого старта
chmod +x quick_start.sh
./quick_start.sh

# Или вручную:
docker-compose up -d
```

### 4. Проверка работоспособности
```bash
# Проверка здоровья
curl http://localhost:8000/health

# Тестирование API
python test_api.py

# Откройте в браузере:
# - Документация API: http://localhost:8000/docs
# - Веб-интерфейс: http://localhost:8000/frontend/
```

## 📁 Структура проекта

```
stereobrother_bot/
├── src/                    # Исходный код
├── config/                # Конфигурация
├── services/              # Бизнес-логика
├── utils/                 # Утилиты
├── frontend/              # Веб-интерфейс
├── db/                    # Миграции БД
├── Dockerfile             # Контейнеризация
├── docker-compose.yml     # Оркестрация
├── requirements.txt       # Зависимости Python
├── run.py                # Скрипт запуска
├── test_api.py           # Тесты API
└── quick_start.sh        # Автоматический запуск
```

## 🎯 Основные функции

### 1. Улучшение качества аудио
- **Полный микс**: Комплексное улучшение всего трека
- **Отдельные инструменты**: Специализированная обработка:
  - 🥁 Ударные (Drums)
  - 🎸 Гитары (Guitars)
  - 🎸 Бас (Bass)
  - 🎻 Струнные (Strings)
  - 🎹 Пианино (Piano)
  - 🎤 Вокал (Vocals)

### 2. Очистка от шумов
- ✅ Треск (crackle)
- ✅ Шипение (hiss)
- ✅ Фоновый шум (background)
- ✅ Шум оборудования (equipment)

### 3. Разделение на дорожки
- **Базовая конфигурация** (4 дорожки):
  - Вокал
  - Ударные
  - Бас
  - Остальное
- **Расширенная конфигурация** (6 дорожек):
  - Вокал
  - Ударные
  - Бас
  - Гитара
  - Пианино
  - Остальное

### 4. ИИ-мастеринг
- **Подкаст**: Акцент на четкость речи
- **Песня**: Музыкальный баланс и плотность
- **Реклама**: Громкость и "радийный" звук

## 🔧 Команды управления

### Запуск сервисов
```bash
# Основное приложение
python run.py server

# Celery worker (обработка задач)
python run.py worker

# Celery beat (периодические задачи)
python run.py beat

# Все сервисы через Docker
docker-compose up -d
```

### Мониторинг
```bash
# Логи приложения
docker-compose logs -f api

# Логи воркеров
docker-compose logs -f worker

# Мониторинг Celery (Flower)
# Откройте: http://localhost:5555

# Метрики Prometheus
# Откройте: http://localhost:9090
```

### Администрирование
```bash
# Проверка состояния
docker-compose ps

# Перезапуск сервиса
docker-compose restart api

# Обновление контейнеров
docker-compose pull
docker-compose up -d

# Остановка всех сервисов
docker-compose down
```

## 📊 API Эндпоинты

### Аутентификация
```
POST   /api/auth/register  # Регистрация
POST   /api/auth/login     # Вход
POST   /api/auth/refresh   # Обновление токена
```

### Обработка аудио
```
POST   /api/audio/upload   # Загрузка файла
POST   /api/audio/enhance  # Улучшение качества
POST   /api/audio/denoise  # Очистка от шумов
POST   /api/audio/separate # Разделение дорожек
POST   /api/audio/master   # Мастеринг
GET    /api/audio/task/{id}# Статус задачи
GET    /api/audio/history  # История обработок
```

### Пользователь
```
GET    /api/user/profile   # Профиль
GET    /api/user/usage     # Использование лимитов
```

### Система
```
GET    /                   # Информация о приложении
GET    /health             # Проверка здоровья
GET    /metrics            # Метрики Prometheus
```

## 🎮 Примеры использования

### 1. Через веб-интерфейс
1. Откройте http://localhost:8000/frontend/
2. Перетащите аудио файл в область загрузки
3. Выберите тип обработки
4. Нажмите "Начать обработку"
5. Скачайте результат

### 2. Через API (cURL)
```bash
# Регистрация пользователя
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","username":"testuser"}'

# Вход
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'

# Загрузка аудио
curl -X POST http://localhost:8000/api/audio/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@audio.mp3"

# Улучшение качества
curl -X POST http://localhost:8000/api/audio/enhance \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_id":"TASK_ID","mode":"full_mix"}'
```

### 3. Через Python
```python
import requests

# Настройка
BASE_URL = "http://localhost:8000"
TOKEN = "your_jwt_token"

# Загрузка файла
with open("audio.wav", "rb") as f:
    files = {"file": f}
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post(f"{BASE_URL}/api/audio/upload", 
                           files=files, headers=headers)
    task_id = response.json()["task_id"]

# Улучшение качества
data = {"task_id": task_id, "mode": "vocals"}
response = requests.post(f"{BASE_URL}/api/audio/enhance", 
                        json=data, headers=headers)
print(response.json())
```

## ⚙️ Настройка для продакшена

### 1. Безопасность
```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=very-secure-random-string-minimum-32-chars
```

### 2. База данных
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
# Рекомендуется использовать облачные БД:
# - AWS RDS
# - Google Cloud SQL
# - Azure Database for PostgreSQL
```

### 3. Хранилище файлов
```env
STORAGE_TYPE=s3
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET_NAME=stereobrother-audio
S3_REGION=us-east-1
```

### 4. Платежная система
```env
PAYMENT_PROVIDER=yookassa
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key
```

### 5. Мониторинг
```env
ENABLE_METRICS=true
# Настройте алерты в Prometheus
# Настройте дашборды в Grafana
```

## 🚨 Устранение неполадок

### Проблема: Приложение не запускается
```bash
# Проверьте логи
docker-compose logs api

# Проверьте порты
netstat -tulpn | grep :8000

# Проверьте зависимости
pip install -r requirements.txt
```

### Проблема: База данных недоступна
```bash
# Проверьте подключение
docker-compose exec db psql -U postgres -c "\l"

# Пересоздайте БД
docker-compose down -v
docker-compose up -d db
```

### Проблема: Redis недоступен
```bash
# Проверьте подключение
docker-compose exec redis redis-cli ping

# Перезапустите Redis
docker-compose restart redis
```

### Проблема: Высокая загрузка CPU
```bash
# Мониторинг ресурсов
docker stats

# Увеличьте количество воркеров
docker-compose up --scale worker=4 -d
```

## 📈 Масштабирование

### Горизонтальное масштабирование
```bash
# Увеличение API инстансов
docker-compose up --scale api=3 -d

# Увеличение воркеров
docker-compose up --scale worker=4 -d

# Балансировка нагрузки
# Настройте Nginx или облачный балансировщик
```

### Вертикальное масштабирование
```yaml
# В docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## 🔄 Обновление

```bash
# Остановка приложения
docker-compose down

# Создание резервной копии
./scripts/backup.sh

# Получение обновлений
git pull origin main

# Обновление образов
docker-compose pull

# Запуск миграций
docker-compose run --rm api alembic upgrade head

# Запуск приложения
docker-compose up -d

# Проверка работоспособности
./scripts/health_check.sh
```

## 📞 Поддержка

- **Документация**: http://localhost:8000/docs
- **Техническая поддержка**: support@stereobrother.com
- **Telegram канал**: https://t.me/stereobrother
- **Issues**: GitHub Issues

## 🎉 Поздравляем!

Вы успешно запустили StereoBrother Bot! 🎧

Дальнейшие шаги:
1. Настройте платежную систему для монетизации
2. Добавьте свои модели ИИ для улучшения качества
3. Настройте мониторинг и алерты
4. Протестируйте на реальных аудио файлах

Удачи в обработке аудио! ✨
```

## Лицензия

Этот проект лицензирован под MIT License. См. файл LICENSE для подробностей.