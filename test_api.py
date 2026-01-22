#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API StereoBrother Bot
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import aiohttp
import numpy as np
import soundfile as sf

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings


class StereoBrotherTester:
    """Класс для тестирования API StereoBrother Bot"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_connection(self) -> bool:
        """Тест подключения к API"""
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Подключение успешно: {data['app']} v{data['version']}")
                    return True
                else:
                    print(f"✗ Ошибка подключения: {response.status}")
                    return False
        except Exception as e:
            print(f"✗ Ошибка подключения: {e}")
            return False

    async def test_health(self) -> bool:
        """Тест проверки здоровья"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Проверка здоровья: {data['status']}")

                    # Проверяем сервисы
                    services = data.get("services", {})
                    for service, status in services.items():
                        status_icon = "✓" if status else "✗"
                        print(
                            f"  {status_icon} {service}: {'работает' if status else 'не работает'}"
                        )

                    return data["status"] == "healthy"
                else:
                    print(f"✗ Ошибка проверки здоровья: {response.status}")
                    return False
        except Exception as e:
            print(f"✗ Ошибка проверки здоровья: {e}")
            return False

    async def register_user(self, email: str, password: str, username: str) -> bool:
        """Регистрация пользователя"""
        try:
            data = {"email": email, "password": password, "username": username}

            async with self.session.post(
                f"{self.base_url}/api/auth/register", json=data
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    self.user_id = user_data.get("id")
                    print(f"✓ Пользователь зарегистрирован: {user_data['email']}")
                    return True
                else:
                    error = await response.text()
                    print(f"✗ Ошибка регистрации: {response.status} - {error}")
                    return False
        except Exception as e:
            print(f"✗ Ошибка регистрации: {e}")
            return False

    async def login_user(self, email: str, password: str) -> bool:
        """Вход пользователя"""
        try:
            data = {"email": email, "password": password}

            async with self.session.post(
                f"{self.base_url}/api/auth/login", json=data
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.token = token_data.get("access_token")
                    print(f"✓ Пользователь вошел: {email}")
                    return True
                else:
                    error = await response.text()
                    print(f"✗ Ошибка входа: {response.status} - {error}")
                    return False
        except Exception as e:
            print(f"✗ Ошибка входа: {e}")
            return False

    async def get_user_profile(self) -> Optional[Dict]:
        """Получение профиля пользователя"""
        if not self.token:
            print("✗ Токен не установлен")
            return None

        try:
            headers = {"Authorization": f"Bearer {self.token}"}

            async with self.session.get(
                f"{self.base_url}/api/user/profile", headers=headers
            ) as response:
                if response.status == 200:
                    profile = await response.json()
                    print(f"✓ Профиль получен: {profile['username']}")
                    return profile
                else:
                    error = await response.text()
                    print(f"✗ Ошибка получения профиля: {response.status} - {error}")
                    return None
        except Exception as e:
            print(f"✗ Ошибка получения профиля: {e}")
            return None

    async def get_user_usage(self) -> Optional[Dict]:
        """Получение информации об использовании"""
        if not self.token:
            print("✗ Токен не установлен")
            return None

        try:
            headers = {"Authorization": f"Bearer {self.token}"}

            async with self.session.get(
                f"{self.base_url}/api/user/usage", headers=headers
            ) as response:
                if response.status == 200:
                    usage = await response.json()
                    print(f"✓ Информация об использовании получена")
                    print(
                        f"  Дневные генерации: {usage['daily_generations']}/{usage['daily_limit']}"
                    )
                    print(f"  Подписка активна: {usage['subscription_active']}")
                    return usage
                else:
                    error = await response.text()
                    print(f"✗ Ошибка получения информации: {response.status} - {error}")
                    return None
        except Exception as e:
            print(f"✗ Ошибка получения информации: {e}")
            return None

    async def create_test_audio_file(self, filename: str = "test_audio.wav") -> str:
        """Создание тестового аудио файла"""
        try:
            # Создаем простой синусоидальный сигнал
            duration = 5  # секунд
            sample_rate = 44100
            frequency = 440  # Hz (нота A4)

            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = 0.5 * np.sin(2 * np.pi * frequency * t)

            # Добавляем немного шума для тестирования денойзинга
            noise = 0.1 * np.random.randn(len(audio_data))
            audio_data += noise

            # Создаем стерео
            audio_data = np.vstack([audio_data, audio_data]).T

            # Сохраняем файл
            file_path = os.path.join(settings.TEMP_DIR, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            sf.write(file_path, audio_data, sample_rate)

            print(f"✓ Тестовый аудио файл создан: {file_path}")
            return file_path

        except Exception as e:
            print(f"✗ Ошибка создания аудио файла: {e}")
            return ""

    async def upload_audio(self, file_path: str) -> Optional[str]:
        """Загрузка аудио файла"""
        if not self.token:
            print("✗ Токен не установлен")
            return None

        try:
            # Читаем файл
            with open(file_path, "rb") as f:
                file_content = f.read()

            # Создаем форму для загрузки
            data = aiohttp.FormData()
            data.add_field("file", file_content, filename=os.path.basename(file_path))

            headers = {"Authorization": f"Bearer {self.token}"}

            async with self.session.post(
                f"{self.base_url}/api/audio/upload", data=data, headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    task_id = result.get("task_id")
                    print(f"✓ Аудио загружено, ID задачи: {task_id}")
                    return task_id
                else:
                    error = await response.text()
                    print(f"✗ Ошибка загрузки аудио: {response.status} - {error}")
                    return None

        except Exception as e:
            print(f"✗ Ошибка загрузки аудио: {e}")
            return None

    async def enhance_audio(self, task_id: str, mode: str = "full_mix") -> bool:
        """Улучшение качества аудио"""
        if not self.token:
            print("✗ Токен не установлен")
            return False

        try:
            data = {"task_id": task_id, "mode": mode}

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

            async with self.session.post(
                f"{self.base_url}/api/audio/enhance", json=data, headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✓ Улучшение запущено: {result['message']}")
                    return True
                else:
                    error = await response.text()
                    print(f"✗ Ошибка улучшения аудио: {response.status} - {error}")
                    return False

        except Exception as e:
            print(f"✗ Ошибка улучшения аудио: {e}")
            return False

    async def denoise_audio(self, task_id: str) -> bool:
        """Очистка аудио от шумов"""
        if not self.token:
            print("✗ Токен не установлен")
            return False

        try:
            data = {
                "task_id": task_id,
                "noise_types": ["crackle", "hiss", "background"],
                "intensity": 0.7,
            }

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

            async with self.session.post(
                f"{self.base_url}/api/audio/denoise", json=data, headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✓ Очистка запущена: {result['message']}")
                    return True
                else:
                    error = await response.text()
                    print(f"✗ Ошибка очистки аудио: {response.status} - {error}")
                    return False

        except Exception as e:
            print(f"✗ Ошибка очистки аудио: {e}")
            return False

    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Получение статуса задачи"""
        if not self.token:
            print("✗ Токен не установлен")
            return None

        try:
            headers = {"Authorization": f"Bearer {self.token}"}

            async with self.session.get(
                f"{self.base_url}/api/audio/task/{task_id}", headers=headers
            ) as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"✓ Статус задачи {task_id}: {status['status']}")
                    return status
                else:
                    error = await response.text()
                    print(f"✗ Ошибка получения статуса: {response.status} - {error}")
                    return None

        except Exception as e:
            print(f"✗ Ошибка получения статуса: {e}")
            return None

    async def run_comprehensive_test(self):
        """Запуск комплексного тестирования"""
        print("=" * 60)
        print("Комплексное тестирование StereoBrother Bot API")
        print("=" * 60)

        # Тест подключения
        print("\n1. Тест подключения к API:")
        if not await self.test_connection():
            return False

        # Тест здоровья
        print("\n2. Тест проверки здоровья:")
        if not await self.test_health():
            return False

        # Регистрация пользователя
        print("\n3. Тест регистрации пользователя:")
        test_email = f"test_{os.getpid()}@stereobrother.com"
        test_password = "TestPassword123!"
        test_username = f"testuser_{os.getpid()}"

        if not await self.register_user(test_email, test_password, test_username):
            # Если пользователь уже существует, пробуем войти
            print("  Пользователь уже существует, пробуем войти...")
            if not await self.login_user(test_email, test_password):
                return False
        else:
            # Если регистрация успешна, входим
            if not await self.login_user(test_email, test_password):
                return False

        # Получение профиля
        print("\n4. Тест получения профиля:")
        profile = await self.get_user_profile()
        if not profile:
            return False

        # Получение информации об использовании
        print("\n5. Тест получения информации об использовании:")
        usage = await self.get_user_usage()
        if not usage:
            return False

        # Создание тестового аудио файла
        print("\n6. Создание тестового аудио файла:")
        audio_file = await self.create_test_audio_file()
        if not audio_file:
            return False

        # Загрузка аудио
        print("\n7. Тест загрузки аудио:")
        task_id = await self.upload_audio(audio_file)
        if not task_id:
            return False

        # Ожидание обработки загрузки
        print("\n8. Ожидание обработки загрузки...")
        await asyncio.sleep(2)

        # Проверка статуса задачи
        status = await self.get_task_status(task_id)
        if not status:
            return False

        # Тест улучшения аудио
        print("\n9. Тест улучшения качества аудио:")
        if not await self.enhance_audio(task_id, "full_mix"):
            return False

        # Ожидание обработки улучшения
        print("\n10. Ожидание обработки улучшения...")
        await asyncio.sleep(3)

        # Тест очистки аудио
        print("\n11. Тест очистки аудио от шумов:")
        if not await self.denoise_audio(task_id):
            return False

        # Ожидание обработки очистки
        print("\n12. Ожидание обработки очистки...")
        await asyncio.sleep(3)

        # Финальная проверка статуса
        print("\n13. Финальная проверка статуса задачи:")
        final_status = await self.get_task_status(task_id)

        print("\n" + "=" * 60)
        print("✅ Комплексное тестирование завершено успешно!")
        print("=" * 60)

        return True


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования StereoBrother Bot API")
    print(f"📡 URL API: http://localhost:{settings.PORT}")

    async with StereoBrotherTester(f"http://localhost:{settings.PORT}") as tester:
        success = await tester.run_comprehensive_test()

        if success:
            print("\n🎉 Все тесты пройдены успешно!")
            print("\n📋 Следующие шаги:")
            print("1. Откройте документацию API: http://localhost:8000/docs")
            print("2. Проверьте логи приложения: tail -f logs/app.log")
            print("3. Настройте переменные окружения в .env файле")
            print("4. Запустите Celery worker: python run.py worker")
            return 0
        else:
            print("\n❌ Тестирование завершено с ошибками")
            print("\n🔧 Рекомендации по устранению проблем:")
            print("1. Убедитесь, что приложение запущено: python run.py server")
            print("2. Проверьте настройки в .env файле")
            print("3. Проверьте логи приложения: tail -f logs/app.log")
            print("4. Убедитесь, что все зависимости установлены")
            return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 Тестирование прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
