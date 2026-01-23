#!/bin/bash

# StereoBrother Bot - GitHub Sync Script
# Этот скрипт упрощает синхронизацию с GitHub репозиторием

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функция для вывода заголовка
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN} StereoBrother Bot - GitHub Sync${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Функция для проверки наличия git
check_git() {
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git не установлен!${NC}"
        echo "Установите git:"
        echo "  macOS: brew install git"
        echo "  Ubuntu/Debian: sudo apt-get install git"
        echo "  Windows: https://git-scm.com/download/win"
        exit 1
    fi
}

# Функция для проверки директории
check_directory() {
    if [ ! -f "README.md" ] || [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}❌ Вы не в корневой директории проекта!${NC}"
        echo "Перейдите в директорию stereobrother_bot"
        exit 1
    fi
}

# Функция для проверки remote репозитория
check_remote() {
    if ! git remote | grep -q origin; then
        echo -e "${RED}❌ Remote репозиторий не настроен!${NC}"
        echo "Настройте remote репозиторий:"
        echo "  git remote add origin https://github.com/kamaero/stereobrother_bot.git"
        echo ""
        echo "Или используйте скрипт: ./push_to_github.sh"
        exit 1
    fi
}

# Функция для вывода статуса
show_status() {
    echo -e "${CYAN}📊 Текущий статус:${NC}"
    echo ""
    
    # Текущая ветка
    current_branch=$(git branch --show-current)
    echo -e "${YELLOW}Текущая ветка:${NC} ${GREEN}$current_branch${NC}"
    
    # Remote URL
    remote_url=$(git remote get-url origin)
    echo -e "${YELLOW}Remote URL:${NC} ${CYAN}$remote_url${NC}"
    
    echo ""
    echo -e "${CYAN}Изменения в рабочей директории:${NC}"
    git status --short
    
    echo ""
}

# Функция для получения изменений с GitHub
pull_changes() {
    echo -e "${BLUE}⬇️  Получение изменений с GitHub...${NC}"
    echo ""
    
    # Получаем информацию о ветках
    echo -e "${YELLOW}Доступные ветки на GitHub:${NC}"
    git fetch origin
    git branch -r | grep origin/ | sed 's/origin\///'
    
    echo ""
    echo -e "${YELLOW}Выберите действие:${NC}"
    echo "1) Получить изменения для текущей ветки (git pull)"
    echo "2) Получить все изменения без слияния (git fetch)"
    echo "3) Переключиться на другую ветку"
    echo "4) Отмена"
    echo ""
    
    read -p "Ваш выбор (1-4): " pull_choice
    
    case $pull_choice in
        1)
            echo -e "${BLUE}Выполняем git pull...${NC}"
            if git pull origin "$current_branch"; then
                echo -e "${GREEN}✅ Изменения успешно получены и объединены${NC}"
            else
                echo -e "${RED}❌ Ошибка при получении изменений${NC}"
                echo "Возможны конфликты. Проверьте статус: git status"
            fi
            ;;
        2)
            echo -e "${BLUE}Выполняем git fetch...${NC}"
            git fetch --all
            echo -e "${GREEN}✅ Все изменения получены${NC}"
            echo "Теперь вы можете:"
            echo "  - Проверить изменения: git log origin/$current_branch..$current_branch"
            echo "  - Слить изменения: git merge origin/$current_branch"
            echo "  - Перебазировать: git rebase origin/$current_branch"
            ;;
        3)
            echo -e "${YELLOW}Доступные ветки:${NC}"
            git branch -a
            echo ""
            read -p "Введите имя ветки для переключения: " branch_name
            if git checkout "$branch_name"; then
                echo -e "${GREEN}✅ Переключено на ветку $branch_name${NC}"
                current_branch="$branch_name"
            else
                echo -e "${RED}❌ Ошибка при переключении ветки${NC}"
            fi
            ;;
        4)
            echo -e "${YELLOW}Отмена операции${NC}"
            return
            ;;
        *)
            echo -e "${RED}❌ Неверный выбор${NC}"
            ;;
    esac
}

# Функция для отправки изменений на GitHub
push_changes() {
    echo -e "${BLUE}⬆️  Отправка изменений на GitHub...${NC}"
    echo ""
    
    # Проверяем есть ли что коммитить
    if git status --porcelain | grep -q .; then
        echo -e "${YELLOW}Обнаружены изменения:${NC}"
        git status --short
        
        echo ""
        echo -e "${YELLOW}Выберите действие:${NC}"
        echo "1) Добавить все изменения и сделать коммит"
        echo "2) Выбрать файлы для добавления"
        echo "3) Только отправить существующие коммиты"
        echo "4) Отмена"
        echo ""
        
        read -p "Ваш выбор (1-4): " push_choice
        
        case $push_choice in
            1)
                echo -e "${YELLOW}Введите сообщение коммита:${NC}"
                read commit_message
                
                if [ -z "$commit_message" ]; then
                    commit_message="Update $(date '+%Y-%m-%d %H:%M:%S')"
                fi
                
                echo -e "${BLUE}Добавляем все изменения...${NC}"
                git add .
                
                echo -e "${BLUE}Создаем коммит...${NC}"
                if git commit -m "$commit_message"; then
                    echo -e "${GREEN}✅ Коммит создан${NC}"
                else
                    echo -e "${YELLOW}⚠️  Не удалось создать коммит (возможно, нет изменений)${NC}"
                fi
                ;;
            2)
                echo -e "${YELLOW}Измененные файлы:${NC}"
                git status --short
                echo ""
                echo -e "${YELLOW}Введите имена файлов для добавления (через пробел):${NC}"
                read files_to_add
                
                if [ -n "$files_to_add" ]; then
                    git add $files_to_add
                    echo -e "${GREEN}✅ Файлы добавлены${NC}"
                    
                    echo -e "${YELLOW}Введите сообщение коммита:${NC}"
                    read commit_message
                    
                    if [ -z "$commit_message" ]; then
                        commit_message="Update selected files $(date '+%Y-%m-%d %H:%M:%S')"
                    fi
                    
                    git commit -m "$commit_message"
                    echo -e "${GREEN}✅ Коммит создан${NC}"
                fi
                ;;
            3)
                echo -e "${BLUE}Пропускаем этап коммита...${NC}"
                ;;
            4)
                echo -e "${YELLOW}Отмена операции${NC}"
                return
                ;;
            *)
                echo -e "${RED}❌ Неверный выбор${NC}"
                return
                ;;
        esac
    else
        echo -e "${GREEN}✅ Нет изменений для коммита${NC}"
    fi
    
    # Отправляем изменения
    echo ""
    echo -e "${BLUE}Отправляем изменения на GitHub...${NC}"
    
    if git push origin "$current_branch"; then
        echo -e "${GREEN}✅ Изменения успешно отправлены на GitHub${NC}"
        
        # Проверяем, нужно ли установить upstream
        if ! git branch --show-current | grep -q "\[.*\]"; then
            echo -e "${YELLOW}Устанавливаем upstream для ветки...${NC}"
            git push --set-upstream origin "$current_branch"
        fi
    else
        echo -e "${RED}❌ Ошибка при отправке изменений${NC}"
        echo "Возможные причины:"
        echo "  - Нет доступа к репозиторию"
        echo "  - Конфликты с удаленной веткой"
        echo "  - Требуется pull перед push"
        echo ""
        echo "Попробуйте: git pull --rebase origin $current_branch"
    fi
}

# Функция для полной синхронизации
full_sync() {
    echo -e "${CYAN}🔄 Полная синхронизация...${NC}"
    echo ""
    
    # Получаем изменения
    echo -e "${BLUE}1. Получаем изменения с GitHub...${NC}"
    git fetch origin
    
    # Проверяем, нужно ли обновить текущую ветку
    current_branch=$(git branch --show-current)
    if git log HEAD..origin/"$current_branch" --oneline | grep -q .; then
        echo -e "${YELLOW}Есть новые изменения на GitHub для ветки $current_branch${NC}"
        read -p "Обновить локальную ветку? (y/n): " update_choice
        if [[ $update_choice == "y" || $update_choice == "Y" ]]; then
            git pull origin "$current_branch"
        fi
    fi
    
    # Отправляем изменения
    echo ""
    echo -e "${BLUE}2. Отправляем изменения на GitHub...${NC}"
    if git status --porcelain | grep -q .; then
        echo -e "${YELLOW}Обнаружены локальные изменения${NC}"
        read -p "Добавить и отправить изменения? (y/n): " push_choice
        if [[ $push_choice == "y" || $push_choice == "Y" ]]; then
            git add .
            git commit -m "Auto-sync $(date '+%Y-%m-%d %H:%M:%S')" || true
            git push origin "$current_branch"
        fi
    else
        echo -e "${GREEN}✅ Нет локальных изменений для отправки${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Полная синхронизация завершена${NC}"
}

# Функция для просмотра истории
view_history() {
    echo -e "${CYAN}📜 История коммитов:${NC}"
    echo ""
    
    echo -e "${YELLOW}Выберите формат:${NC}"
    echo "1) Краткий (последние 10 коммитов)"
    echo "2) Подробный (последние 5 коммитов)"
    echo "3) Графический (git log --graph)"
    echo "4) Сравнение с GitHub"
    echo ""
    
    read -p "Ваш выбор (1-4): " history_choice
    
    case $history_choice in
        1)
            git log --oneline -10
            ;;
        2)
            git log -5
            ;;
        3)
            git log --graph --oneline -15
            ;;
        4)
            current_branch=$(git branch --show-current)
            echo -e "${YELLOW}Коммиты на GitHub, которых нет локально:${NC}"
            git log origin/"$current_branch".."$current_branch" --oneline || echo "Нет таких коммитов"
            echo ""
            echo -e "${YELLOW}Локальные коммиты, которых нет на GitHub:${NC}"
            git log "$current_branch"..origin/"$current_branch" --oneline || echo "Нет таких коммитов"
            ;;
        *)
            echo -e "${RED}❌ Неверный выбор${NC}"
            ;;
    esac
}

# Основное меню
main_menu() {
    while true; do
        echo ""
        echo -e "${BLUE}========================================${NC}"
        echo -e "${GREEN} МЕНЮ СИНХРОНИЗАЦИИ GITHUB${NC}"
        echo -e "${BLUE}========================================${NC}"
        echo ""
        echo "1) 📊 Показать статус"
        echo "2) ⬇️  Получить изменения с GitHub"
        echo "3) ⬆️  Отправить изменения на GitHub"
        echo "4) 🔄 Полная синхронизация"
        echo "5) 📜 Просмотреть историю"
        echo "6) 🌿 Управление ветками"
        echo "7)