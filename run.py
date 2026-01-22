#!/usr/bin/env python3
"""
Скрипт запуска приложения StereoBrother Bot
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.main import app


def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.FileHandler(settings.LOG_FILE),
            logging.StreamHandler(),
        ],
    )


def check_dependencies():
    """Проверка зависимостей"""
    import importlib
    import subprocess

    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "librosa",
        "soundfile",
        "numpy",
        "scipy",
    ]

    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"Отсутствуют необходимые пакеты: {', '.join(missing_packages)}")
        print("Установите их с помощью: pip install -r requirements.txt")
        return False

    # Проверяем наличие FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Предупреждение: FFmpeg не найден. Некоторые функции могут не работать.")
        print("Установите FFmpeg:")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  macOS: brew install ffmpeg")
        print("  Windows: скачайте с https://ffmpeg.org/")

    return True


def create_directories():
    """Создание необходимых директорий"""
    directories = [
        settings.TEMP_DIR,
        settings.LOCAL_STORAGE_PATH,
        settings.AI_MODELS_PATH,
        os.path.dirname(settings.LOG_FILE),
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Создана директория: {directory}")


def run_server(host: str, port: int, reload: bool = False):
    """Запуск сервера"""
    import uvicorn

    print(f"Запуск StereoBrother Bot v{settings.APP_VERSION}")
    print(f"Среда: {settings.ENVIRONMENT}")
    print(f"Отладка: {settings.DEBUG}")
    print(f"Сервер: http://{host}:{port}")
    print(f"Документация: http://{host}:{port}/docs")
    print(f"Проверка здоровья: http://{host}:{port}/health")
    print("\nНажмите Ctrl+C для остановки\n")

    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info" if settings.DEBUG else "warning",
        workers=settings.WORKERS if not reload else 1,
    )


def run_worker():
    """Запуск Celery worker"""
    from src.tasks import celery_app

    print("Запуск Celery worker...")
    print("Для мониторинга перейдите по адресу: http://localhost:5555")

    worker = celery_app.Worker(
        loglevel="INFO",
        concurrency=4,
        pool="solo",  # Для Windows используйте 'solo', для Linux/Mac - 'prefork'
    )
    worker.start()


def run_beat():
    """Запуск Celery beat"""
    from src.tasks import celery_app

    print("Запуск Celery beat...")

    beat = celery_app.Beat(
        loglevel="INFO",
    )
    beat.run()


def run_tests():
    """Запуск тестов"""
    import subprocess

    print("Запуск тестов...")

    result = subprocess.run(
        ["pytest", "tests/", "-v", "--cov=src", "--cov-report=term-missing"],
        cwd=project_root,
    )

    return result.returncode == 0


def run_migrations():
    """Запуск миграций базы данных"""
    print("Запуск миграций...")

    # Здесь будет логика миграций
    # Для начала можно просто выполнить SQL скрипт
    db_init_file = project_root / "db" / "init.sql"
    if db_init_file.exists():
        print(f"Найден файл инициализации БД: {db_init_file}")
        print("Для выполнения миграций используйте Alembic или другую систему миграций")
    else:
        print("Файл инициализации БД не найден")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(
        description="StereoBrother Bot - ИИ обработка аудио"
    )
    subparsers = parser.add_subparsers(dest="command", help="Команда")

    # Команда запуска сервера
    server_parser = subparsers.add_parser("server", help="Запуск сервера")
    server_parser.add_argument("--host", default=settings.HOST, help="Хост сервера")
    server_parser.add_argument(
        "--port", type=int, default=settings.PORT, help="Порт сервера"
    )
    server_parser.add_argument(
        "--reload", action="store_true", help="Автоматическая перезагрузка"
    )

    # Команда запуска worker
    subparsers.add_parser("worker", help="Запуск Celery worker")

    # Команда запуска beat
    subparsers.add_parser("beat", help="Запуск Celery beat")

    # Команда запуска тестов
    subparsers.add_parser("test", help="Запуск тестов")

    # Команда запуска миграций
    subparsers.add_parser("migrate", help="Запуск миграций БД")

    # Команда проверки
    subparsers.add_parser("check", help="Проверка системы")

    args = parser.parse_args()

    # Настройка логирования
    setup_logging()

    if args.command == "server":
        if not check_dependencies():
            sys.exit(1)
        create_directories()
        run_server(args.host, args.port, args.reload)

    elif args.command == "worker":
        if not check_dependencies():
            sys.exit(1)
        create_directories()
        run_worker()

    elif args.command == "beat":
        if not check_dependencies():
            sys.exit(1)
        run_beat()

    elif args.command == "test":
        success = run_tests()
        sys.exit(0 if success else 1)

    elif args.command == "migrate":
        run_migrations()

    elif args.command == "check":
        print("Проверка системы...")
        if check_dependencies():
            print("✓ Все зависимости установлены")
        else:
            print("✗ Некоторые зависимости отсутствуют")

        create_directories()
        print("✓ Директории созданы")

        # Проверяем доступность порта
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((settings.HOST, settings.PORT))
            print(f"✓ Порт {settings.PORT} доступен")
        except OSError:
            print(f"✗ Порт {settings.PORT} занят")
        finally:
            sock.close()

        print("\nПроверка завершена")

    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПриложение остановлено")
        sys.exit(0)
    except Exception as e:
        print(f"Ошибка: {e}")
        if settings.DEBUG:
            import traceback

            traceback.print_exc()
        sys.exit(1)
