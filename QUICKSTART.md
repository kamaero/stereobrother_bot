# 🚀 Быстрый старт StereoBrother Bot на M2

## В 3 шага:

### 1️⃣ Установка (5-10 минут)
```bash
cd ~/stereobrother_bot
chmod +x setup_m2.sh
./setup_m2.sh
```

### 2️⃣ Запуск (3 терминала)

**Терминал 1 - API:**
```bash
source venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Терминал 2 - Celery Worker:**
```bash
source venv/bin/activate
celery -A src.tasks.celery_app worker --loglevel=info --concurrency=2
```

**Терминал 3 - Celery Beat:**
```bash
source venv/bin/activate
celery -A src.tasks.celery_app beat --loglevel=info
```

### 3️⃣ Проверка

Откройте в браузере: **http://localhost:8000/docs**

## ✅ Готово!

Теперь можете:
- Регистрировать пользователей
- Загружать аудио
- Обрабатывать через AI
- Разделять треки
- Улучшать качество

---

**Проблемы?** См. INSTALL_M2.md или README_РАБОТАЕТ.md
