# Инструкции по развертыванию StereoBrother Bot

## Содержание
1. [Быстрое развертывание с Docker](#быстрое-развертывание-с-docker)
2. [Развертывание на сервере](#развертывание-на-сервере)
3. [Развертывание в облаке](#развертывание-в-облаке)
4. [Масштабирование](#масштабирование)
5. [Мониторинг и логирование](#мониторинг-и-логирование)
6. [Резервное копирование](#резервное-копирование)
7. [Обновление](#обновление)
8. [Устранение неполадок](#устранение-неполадок)

## Быстрое развертывание с Docker

### Предварительные требования
- Docker 20.10+
- Docker Compose 2.0+
- 4+ GB RAM
- 20+ GB свободного места на диске

### Шаг 1: Клонирование репозитория
```bash
git clone https://github.com/yourusername/stereobrother_bot.git
cd stereobrother_bot
```

### Шаг 2: Настройка переменных окружения
```bash
cp env.example .env
# Отредактируйте .env файл
nano .env
```

Основные настройки для продакшена:
```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-very-secure-secret-key-change-this
DATABASE_URL=postgresql://user:password@db:5432/stereobrother_db
REDIS_URL=redis://redis:6379/0
```

### Шаг 3: Запуск приложения
```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f api
```

### Шаг 4: Проверка работоспособности
```bash
# Проверка здоровья API
curl http://localhost:8000/health

# Проверка документации
# Откройте в браузере: http://localhost:8000/docs
```

## Развертывание на сервере

### Требования к серверу
- Ubuntu 20.04 LTS или выше
- 4+ ядер CPU
- 8+ GB RAM
- 50+ GB SSD
- Статический IP адрес

### Шаг 1: Установка зависимостей
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Установка системных зависимостей
sudo apt install -y \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    ffmpeg \
    libsndfile1
```

### Шаг 2: Настройка файрвола
```bash
# Настройка UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

### Шаг 3: Настройка Nginx
```bash
# Создание конфигурации Nginx
sudo nano /etc/nginx/sites-available/stereobrother

# Добавьте следующую конфигурацию:
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /storage/ {
        alias /path/to/stereobrother_bot/storage/;
    }
}

# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/stereobrother /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Шаг 4: Настройка SSL
```bash
# Получение SSL сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление сертификатов
sudo systemctl enable certbot.timer
```

### Шаг 5: Настройка systemd для автоматического запуска
```bash
# Создание systemd сервиса
sudo nano /etc/systemd/system/stereobrother.service

# Добавьте следующее:
[Unit]
Description=StereoBrother Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/stereobrother_bot
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target

# Запуск сервиса
sudo systemctl enable stereobrother.service
sudo systemctl start stereobrother.service
```

## Развертывание в облаке

### AWS (Amazon Web Services)

#### Шаг 1: Создание EC2 инстанса
- Тип инстанса: t3.medium или выше
- ОС: Ubuntu 20.04 LTS
- Storage: 50 GB GP2
- Security Group: открыть порты 22, 80, 443

#### Шаг 2: Настройка RDS (база данных)
```bash
# Создание RDS инстанса PostgreSQL
# Параметры:
# - Engine: PostgreSQL 15
# - Instance class: db.t3.micro
# - Storage: 20 GB
# - Multi-AZ: для продакшена
```

#### Шаг 3: Настройка ElastiCache (Redis)
```bash
# Создание ElastiCache кластера Redis
# Параметры:
# - Engine: Redis 7
# - Node type: cache.t3.micro
# - Multi-AZ: для продакшена
```

#### Шаг 4: Настройка S3 (хранилище файлов)
```bash
# Создание S3 бакета
# Параметры:
# - Bucket name: stereobrother-audio
# - Region: ваш регион
# - Versioning: включить
# - Encryption: включить
```

### Google Cloud Platform (GCP)

#### Шаг 1: Создание Compute Engine
- Machine type: e2-medium или выше
- OS: Ubuntu 20.04 LTS
- Boot disk: 50 GB SSD

#### Шаг 2: Настройка Cloud SQL
```bash
# Создание Cloud SQL инстанса
# Параметры:
# - Database: PostgreSQL 15
# - Machine type: db-f1-micro
# - Storage: 20 GB SSD
```

#### Шаг 3: Настройка Memorystore (Redis)
```bash
# Создание Memorystore инстанса
# Параметры:
# - Version: Redis 7
# - Tier: Basic
# - Memory size: 1 GB
```

#### Шаг 4: Настройка Cloud Storage
```bash
# Создание Cloud Storage бакета
# Параметры:
# - Name: stereobrother-audio
# - Location: ваш регион
# - Storage class: Standard
```

### Azure

#### Шаг 1: Создание Virtual Machine
- Size: Standard_B2s или выше
- OS: Ubuntu Server 20.04 LTS
- Disk: 50 GB SSD

#### Шаг 2: Настройка Azure Database for PostgreSQL
```bash
# Создание базы данных
# Параметры:
# - Compute: Basic, 1 vCore
# - Storage: 20 GB
# - Backup: включить
```

#### Шаг 3: Настройка Azure Cache for Redis
```bash
# Создание кэша Redis
# Параметры:
# - Pricing tier: Basic C0
# - Capacity: 250 MB
```

#### Шаг 4: Настройка Blob Storage
```bash
# Создание Storage Account
# Параметры:
# - Performance: Standard
# - Redundancy: LRS
# - Access tier: Hot
```

## Масштабирование

### Горизонтальное масштабирование
```bash
# Увеличение количества API инстансов
docker-compose up --scale api=3 -d

# Увеличение количества воркеров
docker-compose up --scale worker=4 -d

# Настройка балансировщика нагрузки
# Для Nginx добавьте upstream:
upstream stereobrother_api {
    server api_1:8000;
    server api_2:8000;
    server api_3:8000;
}

server {
    location / {
        proxy_pass http://stereobrother_api;
    }
}
```

### Вертикальное масштабирование
```bash
# Увеличение ресурсов контейнеров в docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Автомасштабирование (для облачных провайдеров)

#### AWS Auto Scaling
```yaml
# Создание Auto Scaling Group
# Параметры:
# - Min size: 2
# - Max size: 10
# - Desired capacity: 3
# - Scaling policies: CPU > 70%
```

#### GCP Autoscaler
```yaml
# Создание Managed Instance Group
# Параметры:
# - Min replicas: 2
# - Max replicas: 10
# - Target CPU utilization: 70%
```

## Мониторинг и логирование

### Prometheus + Grafana
```bash
# Запуск мониторинга
docker-compose -f docker-compose.monitoring.yml up -d

# Доступ к интерфейсам:
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

### Настройка алертов
```yaml
# prometheus/alert_rules.yml
groups:
  - name: stereobrother_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Высокий уровень ошибок"
          description: "Более 10% запросов возвращают ошибки"
```

### Централизованное логирование
```bash
# Использование ELK стека
docker-compose -f docker-compose.logging.yml up -d

# Или использование облачных решений:
# - AWS CloudWatch
# - GCP Stackdriver
# - Azure Monitor
```

## Резервное копирование

### Резервное копирование базы данных
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/database"
DB_NAME="stereobrother_db"

# Создание резервной копии
docker exec stereobrother-db pg_dump -U postgres $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Сжатие резервной копии
gzip $BACKUP_DIR/backup_$DATE.sql

# Удаление старых резервных копий (старше 30 дней)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

# Загрузка в облачное хранилище
aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://stereobrother-backups/database/
```

### Резервное копирование файлов
```bash
#!/bin/bash
# backup_files.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/files"
STORAGE_DIR="/path/to/stereobrother_bot/storage"

# Создание резервной копии файлов
tar -czf $BACKUP_DIR/files_$DATE.tar.gz $STORAGE_DIR

# Загрузка в облачное хранилище
aws s3 cp $BACKUP_DIR/files_$DATE.tar.gz s3://stereobrother-backups/files/
```

### Автоматизация резервного копирования
```bash
# Добавление в crontab
crontab -e

# Ежедневное резервное копирование в 2:00
0 2 * * * /path/to/backup.sh

# Еженедельное полное резервное копирование
0 3 * * 0 /path/to/backup_full.sh
```

## Обновление

### Процесс обновления
```bash
# Шаг 1: Остановка приложения
docker-compose down

# Шаг 2: Создание резервной копии
./scripts/backup.sh

# Шаг 3: Получение обновлений
git pull origin main

# Шаг 4: Обновление зависимостей
docker-compose build --no-cache

# Шаг 5: Запуск миграций
docker-compose run --rm api alembic upgrade head

# Шаг 6: Запуск приложения
docker-compose up -d

# Шаг 7: Проверка работоспособности
./scripts/health_check.sh
```

### Blue-Green развертывание
```bash
# Создание синего окружения
docker-compose -f docker-compose.blue.yml up -d

# Тестирование синего окружения
./scripts/test_deployment.sh blue

# Переключение трафика
nginx -s reload

# Остановка зеленого окружения
docker-compose -f docker-compose.green.yml down
```

## Устранение неполадок

### Общие проблемы

#### Проблема: Приложение не запускается
```bash
# Проверка логов
docker-compose logs api

# Проверка состояния контейнеров
docker-compose ps

# Проверка доступности портов
netstat -tulpn | grep :8000
```

#### Проблема: База данных недоступна
```bash
# Проверка подключения к базе данных
docker exec stereobrother-db psql -U postgres -c "\l"

# Проверка логов базы данных
docker-compose logs db
```

#### Проблема: Redis недоступен
```bash
# Проверка подключения к Redis
docker exec stereobrother-redis redis-cli ping

# Проверка использования памяти
docker exec stereobrother-redis redis-cli info memory
```

#### Проблема: Высокая загрузка CPU
```bash
# Мониторинг процессов
docker stats

# Анализ логов
docker-compose logs --tail=100 api | grep -i error

# Проверка метрик
curl http://localhost:8000/metrics | grep process_cpu
```

### Инструменты диагностики

#### Health check скрипт
```bash
#!/bin/bash
# health_check.sh

# Проверка API
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $API_STATUS -eq 200 ]; then
    echo "✓ API работает"
else
    echo "✗ API недоступен: $API_STATUS"
fi

# Проверка базы данных
DB_STATUS=$(docker exec stereobrother-db pg_isready -U postgres)
if [ $? -eq 0 ]; then
    echo "✓ База данных работает"
else
    echo "✗ База данных недоступна"
fi

# Проверка Redis
REDIS_STATUS=$(docker exec stereobrother-redis redis-cli ping)
if [ "$REDIS_STATUS" = "PONG" ]; then
    echo "✓ Redis работает"
else
    echo "✗ Redis недоступен"
fi
```

#### Скрипт мониторинга ресурсов
```bash
#!/bin/bash
# monitor_resources.sh

echo "=== Мониторинг ресурсов ==="
echo "Дата: $(date)"
echo ""

# Использование CPU
echo "CPU использование:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}" | grep stereobrother

echo ""

# Использование памяти
echo "Использование памяти:"
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" | grep stereobrother

echo ""

# Использование диска
echo "Использование диска:"
df -h / | tail -1
```

### Контакты для поддержки

- **Техническая поддержка**: support@stereobrother.com
- **Экстренные случаи**: emergency@stereobrother.com
- **Telegram канал**: https://t.me/stereobrother_support
- **Документация**: https://docs.stereobrother.com

### Полезные команды

```bash
# Быстрый перезапуск
docker-compose restart api

# Очистка временных файлов
docker-compose exec api python -c "from utils.storage import StorageManager; StorageManager().cleanup_old_files()"

# Сброс кэша