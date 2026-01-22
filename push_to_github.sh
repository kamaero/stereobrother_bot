#!/bin/bash

# StereoBrother Bot - GitHub Push Script
# Этот скрипт поможет запушить проект в GitHub

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN} StereoBrother Bot - GitHub Push Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Проверка наличия git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git не установлен!${NC}"
    echo "Установите git:"
    echo "  macOS: brew install git"
    echo "  Ubuntu/Debian: sudo apt-get install git"
    echo "  Windows: https://git-scm.com/download/win"
    exit 1
fi

# Проверка текущей директории
if [ ! -f "README.md" ] || [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Вы не в корневой директории проекта!${NC}"
    echo "Перейдите в директорию stereobrother_bot"
    exit 1
fi

# Проверка статуса git
echo -e "${YELLOW}📊 Проверка статуса git...${NC}"
git status

echo ""
echo -e "${BLUE}📋 ИНСТРУКЦИЯ ПО ПУШИНГУ В GITHUB${NC}"
echo ""

echo -e "${YELLOW}1. Создайте репозиторий на GitHub:${NC}"
echo "   Перейдите на https://github.com/new"
echo "   Заполните данные:"
echo "   - Repository name: stereobrother_bot"
echo "   - Description: Бот для ИИ-обработки и реставрации аудио"
echo "   - Visibility: Public (рекомендуется)"
echo "   - НЕ отмечайте 'Initialize repository'"
echo ""

echo -e "${YELLOW}2. Выберите способ подключения:${NC}"
echo "   a) HTTPS (проще для начала)"
echo "   b) SSH (рекомендуется для безопасности)"
echo ""

read -p "Выберите способ (a/b): " connection_method

case $connection_method in
    a|A)
        echo -e "${YELLOW}Введите ваш GitHub username:${NC}"
        read github_username

        echo -e "${YELLOW}Добавляем remote репозиторий...${NC}"
        git remote add origin "https://github.com/${github_username}/stereobrother_bot.git"

        echo -e "${GREEN}✅ Remote добавлен (HTTPS)${NC}"
        ;;
    b|B)
        echo -e "${YELLOW}Проверяем SSH ключи...${NC}"

        # Проверка существования SSH ключа
        if [ ! -f ~/.ssh/id_rsa.pub ]; then
            echo -e "${RED}❌ SSH ключ не найден!${NC}"
            echo "Создайте SSH ключ:"
            echo "  ssh-keygen -t rsa -b 4096 -C \"your_email@example.com\""
            echo "  eval \"\$(ssh-agent -s)\""
            echo "  ssh-add ~/.ssh/id_rsa"
            echo ""
            echo "Добавьте публичный ключ в GitHub:"
            echo "  cat ~/.ssh/id_rsa.pub"
            echo "  Скопируйте вывод и добавьте в GitHub:"
            echo "  Settings → SSH and GPG keys → New SSH key"
            exit 1
        fi

        echo -e "${YELLOW}Введите ваш GitHub username:${NC}"
        read github_username

        echo -e "${YELLOW}Добавляем remote репозиторий...${NC}"
        git remote set-url origin "git@github.com:${github_username}/stereobrother_bot.git"

        echo -e "${GREEN}✅ Remote добавлен (SSH)${NC}"
        ;;
    *)
        echo -e "${RED}❌ Неверный выбор${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}3. Проверяем remote...${NC}"
git remote -v

echo ""
echo -e "${YELLOW}4. Запушиваем код в GitHub...${NC}"
echo ""

# Пуш основной ветки
echo -e "${BLUE}Запушиваем ветку main...${NC}"
if git push -u origin main; then
    echo -e "${GREEN}✅ Ветка main успешно запушина${NC}"
else
    echo -e "${RED}❌ Ошибка при пуше ветки main${NC}"
    echo "Возможные причины:"
    echo "  - Репозиторий не создан на GitHub"
    echo "  - Проблемы с доступом"
    echo "  - Конфликт с существующим репозиторием"
    exit 1
fi

echo ""

# Пуш ветки develop
echo -e "${BLUE}Запушиваем ветку develop...${NC}"
if git push -u origin develop; then
    echo -e "${GREEN}✅ Ветка develop успешно запушина${NC}"
else
    echo -e "${YELLOW}⚠️  Ветка develop не запушина (может не существовать на GitHub)${NC}"
fi

echo ""

# Пуш тегов
echo -e "${BLUE}Запушиваем теги...${NC}"
if git push --tags; then
    echo -e "${GREEN}✅ Теги успешно запушины${NC}"
else
    echo -e "${YELLOW}⚠️  Теги не запушины${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 ПРОЕКТ УСПЕШНО ЗАПУШЕН В GITHUB!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}📋 ДАЛЬНЕЙШИЕ ШАГИ:${NC}"
echo ""
echo "1. Откройте репозиторий:"
echo "   https://github.com/${github_username}/stereobrother_bot"
echo ""
echo "2. Настройте GitHub Actions:"
echo "   - Перейдите в Settings → Actions → General"
echo "   - Включите Actions для этого репозитория"
echo ""
echo "3. Настройте секреты (Secrets):"
echo "   Settings → Secrets and variables → Actions"
echo "   Добавьте необходимые секреты для деплоя"
echo ""
echo "4. Создайте первый релиз:"
echo "   - Перейдите в Releases → Draft new release"
echo "   - Выберите тег v1.0.0"
echo "   - Добавьте описание из CHANGELOG.md"
echo ""
echo "5. Настройте окружения:"
echo "   Settings → Environments"
echo "   Создайте staging и production"
echo ""
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Ссылки:${NC}"
echo "📚 Документация: PUSH_TO_GITHUB.md"
echo "🚀 Быстрый старт: QUICK_START_GUIDE.md"
echo "⚙️  Развертывание: DEPLOYMENT.md"
echo ""
echo -e "${YELLOW}Удачи в развитии проекта! 🚀${NC}"

# Сделаем скрипт исполняемым
chmod +x "$0"
