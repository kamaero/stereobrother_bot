#!/bin/bash

# StereoBrother Bot - Скрипт быстрого старта
# Автоматизирует установку и запуск проекта

set -e  # Выход при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия команд
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "Команда '$1' не найдена"
        exit 1
    fi
}

# Заголовок
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║      StereoBrother Bot - Быстрый старт              ║"
echo "║      ИИ-обработка и реставрация аудио               ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Проверка зависимостей
print_info "Проверка зависимостей..."

check_command "python3"
check_command "pip3"
check_command "docker"
check_command "docker-compose"

# Проверка версий
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
DOCKER_COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | tr -d ',')

print_info "Python: $PYTHON_VERSION"
print_info "Docker: $DOCKER_VERSION"
print_info "Docker Compose: $DOCKER_COMPOSE_VERSION"

# Создание директорий
print_info "Создание необходимых директорий..."

mkdir -p storage uploads temp logs models
print_success "Директории созданы"

# Настройка переменных окружения
if [ ! -f .env ]; then
    print_info "Создание файла .env из примера..."
    if [ -f env.example ]; then
        cp env.example .env
        print_success "Файл .env создан"
        print_warning "Отредактируйте файл .env перед запуском в продакшене"
    else
        print_error "Файл env.example не найден"
        exit 1
    fi
else
    print_info "Файл .env уже существует"
fi

# Установка Python зависимостей
print_info "Установка Python зависимостей..."

if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
    print_success "Python зависимости установлены"
else
    print_warning "Файл requirements.txt не найден, пропускаем..."
fi

# Сборка Docker образов
print_info "Сборка Docker образов..."

docker-compose build
print_success "Docker образы собраны"

# Запуск базы данных и Redis
print_info "Запуск базы данных и Redis..."

docker-compose up -d db redis
print_success "База данных и Redis запущены"

# Ожидание запуска базы данных
print_info "Ожидание запуска базы данных..."
sleep 10

# Инициализация базы данных
print_info "Инициализация базы данных..."

if [ -f db/init.sql ]; then
    docker-compose exec -T db psql -U postgres -d stereobrother_db < db/init.sql
    print_success "База данных инициализирована"
else
    print_warning "Файл инициализации БД не найден"
fi

# Запуск основного приложения
print_info "Запуск основного приложения..."

docker-compose up -d api
print_success "Основное приложение запущено"

# Запуск Celery worker
print_info "Запуск Celery worker..."

docker-compose up -d worker
print_success "Celery worker запущен"

# Запуск Celery beat
print_info "Запуск Celery beat..."

docker-compose up -d beat
print_success "Celery beat запущен"

# Запуск Flower для мониторинга
print_info "Запуск Flower для мониторинга..."

docker-compose up -d flower
print_success "Flower запущен"

# Проверка состояния
print_info "Проверка состояния сервисов..."

sleep 5
docker-compose ps

# Проверка здоровья API
print_info "Проверка здоровья API..."

API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")

if [ "$API_HEALTH" = "200" ]; then
    print_success "API работает корректно"
else
    print_warning "API может быть недоступен (код: $API_HEALTH)"
fi

# Вывод информации для пользователя
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║          Установка завершена успешно!               ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo "📊 Сервисы доступны по адресам:"
echo "   • API и документация: http://localhost:8000"
echo "   • Документация Swagger: http://localhost:8000/docs"
echo "   • Документация ReDoc: http://localhost:8000/redoc"
echo "   • Проверка здоровья: http://localhost:8000/health"
echo "   • Flower (мониторинг Celery): http://localhost:5555"
echo ""
echo "🛠️  Полезные команды:"
echo "   • Просмотр логов: docker-compose logs -f [service]"
echo "   • Остановка: docker-compose down"
echo "   • Перезапуск: docker-compose restart [service]"
echo "   • Обновление: docker-compose pull && docker-compose up -d"
echo ""
echo "🧪 Тестирование:"
echo "   • Запуск тестов: python test_api.py"
echo "   • Тест API: python run.py test"
echo ""
echo "⚙️  Настройка:"
echo "   1. Отредактируйте файл .env для продакшена"
echo "   2. Настройте платежную систему"
echo "   3. Настройте хранилище файлов (S3 рекомендуется)"
echo ""
echo "📈 Мониторинг:"
echo "   • Логи приложения: tail -f logs/app.log"
echo "   • Логи базы данных: docker-compose logs -f db"
echo "   • Логи Redis: docker-compose logs -f redis"
echo ""
echo "🚀 Для начала работы откройте http://localhost:8000/docs"
echo ""

# Запуск тестового скрипта
read -p "Запустить тестовый скрипт? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Запуск тестового скрипта..."
    if [ -f test_api.py ]; then
        python3 test_api.py
    else
        print_warning "Тестовый скрипт не найден"
    fi
fi

echo ""
print_success "StereoBrother Bot готов к работе! 🎧✨"
