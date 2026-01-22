"""
Сервис для управления пользователями и аутентификацией
"""

import asyncio
import hashlib
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import jwt
from pydantic import ValidationError

from config.settings import settings
from models.schemas import TokenResponse, UserResponse, UserUsage


class UserManager:
    """
    Сервис для управления пользователями, аутентификацией и лимитами
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.users: Dict[str, Dict] = {}
        self.sessions: Dict[str, Dict] = {}
        self.user_usage: Dict[str, Dict] = {}
        self.refresh_tokens: Dict[str, Dict] = {}

    async def initialize(self):
        """
        Инициализация сервиса
        """
        self.logger.info("Инициализация UserManager...")

        # Загружаем тестовых пользователей (для разработки)
        if settings.DEBUG:
            await self._load_test_users()

        self.logger.info("UserManager инициализирован")

    async def shutdown(self):
        """
        Завершение работы сервиса
        """
        self.logger.info("Завершение работы UserManager...")

        # Очищаем старые сессии
        await self._cleanup_old_sessions()

        self.logger.info("UserManager завершил работу")

    async def register_user(
        self, email: str, password: str, username: str
    ) -> UserResponse:
        """
        Регистрация нового пользователя

        Args:
            email: Email пользователя
            password: Пароль
            username: Имя пользователя

        Returns:
            Информация о зарегистрированном пользователе

        Raises:
            ValueError: Если пользователь уже существует или данные невалидны
        """
        # Проверяем, существует ли пользователь
        for user in self.users.values():
            if user["email"] == email:
                raise ValueError("Пользователь с таким email уже существует")
            if user["username"] == username:
                raise ValueError("Пользователь с таким именем уже существует")

        # Создаем хеш пароля
        password_hash = self._hash_password(password)

        # Создаем ID пользователя
        user_id = str(uuid.uuid4())

        # Создаем пользователя
        user = {
            "id": user_id,
            "email": email,
            "username": username,
            "password_hash": password_hash,
            "is_active": True,
            "is_verified": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_login": None,
            "subscription": {
                "active": False,
                "plan": None,
                "started_at": None,
                "ends_at": None,
                "auto_renew": False,
            },
        }

        # Сохраняем пользователя
        self.users[user_id] = user

        # Инициализируем использование
        self.user_usage[user_id] = {
            "daily_generations": 0,
            "monthly_generations": 0,
            "total_generations": 0,
            "last_processing_date": None,
            "daily_reset_date": datetime.now().date(),
            "monthly_reset_date": datetime.now().replace(day=1).date(),
        }

        self.logger.info(f"Зарегистрирован новый пользователь: {email}")

        return UserResponse(
            id=user_id,
            email=email,
            username=username,
            is_active=True,
            is_verified=False,
            created_at=user["created_at"],
            updated_at=user["updated_at"],
        )

    async def login_user(self, email: str, password: str) -> TokenResponse:
        """
        Вход пользователя в систему

        Args:
            email: Email пользователя
            password: Пароль

        Returns:
            Токены доступа

        Raises:
            ValueError: Если неверные учетные данные
        """
        # Ищем пользователя
        user = None
        for u in self.users.values():
            if u["email"] == email:
                user = u
                break

        if not user:
            raise ValueError("Неверный email или пароль")

        # Проверяем пароль
        if not self._verify_password(password, user["password_hash"]):
            raise ValueError("Неверный email или пароль")

        # Проверяем, активен ли пользователь
        if not user["is_active"]:
            raise ValueError("Аккаунт деактивирован")

        # Обновляем время последнего входа
        user["last_login"] = datetime.now()
        user["updated_at"] = datetime.now()

        # Сбрасываем дневные лимиты если нужно
        await self._reset_daily_limits_if_needed(user["id"])

        # Создаем токены
        tokens = await self._create_tokens(user["id"])

        self.logger.info(f"Пользователь вошел в систему: {email}")

        return tokens

    async def verify_token(self, token: str) -> Optional[Dict]:
        """
        Проверка токена доступа

        Args:
            token: JWT токен

        Returns:
            Информация о пользователе или None
        """
        try:
            # Декодируем токен
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": True},
            )

            user_id = payload.get("sub")
            if not user_id:
                return None

            # Проверяем, существует ли пользователь
            user = self.users.get(user_id)
            if not user or not user["is_active"]:
                return None

            # Проверяем, не отозван ли токен
            session_id = payload.get("sid")
            if session_id and session_id in self.sessions:
                session = self.sessions[session_id]
                if session.get("revoked", False):
                    return None

            return user

        except jwt.ExpiredSignatureError:
            self.logger.warning("Токен истек")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Неверный токен: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при проверке токена: {str(e)}")
            return None

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Обновление access токена

        Args:
            refresh_token: Refresh токен

        Returns:
            Новые токены

        Raises:
            ValueError: Если refresh токен невалиден
        """
        try:
            # Проверяем refresh токен
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": True},
            )

            user_id = payload.get("sub")
            token_id = payload.get("jti")

            if not user_id or not token_id:
                raise ValueError("Неверный refresh токен")

            # Проверяем, существует ли пользователь
            user = self.users.get(user_id)
            if not user or not user["is_active"]:
                raise ValueError("Пользователь не найден или неактивен")

            # Проверяем, не отозван ли refresh токен
            if token_id in self.refresh_tokens:
                token_info = self.refresh_tokens[token_id]
                if token_info.get("revoked", False):
                    raise ValueError("Refresh токен отозван")

                # Помечаем старый токен как использованный
                token_info["used"] = True
                token_info["used_at"] = datetime.now()

            # Создаем новые токены
            tokens = await self._create_tokens(user_id)

            self.logger.info(f"Токены обновлены для пользователя: {user['email']}")

            return tokens

        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh токен истек")
        except jwt.InvalidTokenError:
            raise ValueError("Неверный refresh токен")
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении токена: {str(e)}")
            raise ValueError("Ошибка при обновлении токена")

    async def get_user_profile(self, user_id: str) -> Optional[UserResponse]:
        """
        Получение профиля пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Профиль пользователя или None
        """
        user = self.users.get(user_id)
        if not user:
            return None

        return UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            is_active=user["is_active"],
            is_verified=user["is_verified"],
            created_at=user["created_at"],
            updated_at=user["updated_at"],
        )

    async def get_user_usage(self, user_id: str) -> UserUsage:
        """
        Получение информации об использовании лимитов

        Args:
            user_id: ID пользователя

        Returns:
            Информация об использовании
        """
        usage = self.user_usage.get(user_id, {})
        user = self.users.get(user_id, {})

        return UserUsage(
            user_id=user_id,
            daily_generations=usage.get("daily_generations", 0),
            monthly_generations=usage.get("monthly_generations", 0),
            total_generations=usage.get("total_generations", 0),
            last_processing_date=usage.get("last_processing_date"),
            subscription_active=user.get("subscription", {}).get("active", False),
            subscription_ends_at=user.get("subscription", {}).get("ends_at"),
        )

    async def can_process_audio(self, user_id: str) -> bool:
        """
        Проверка, может ли пользователь обрабатывать аудио

        Args:
            user_id: ID пользователя

        Returns:
            True если может обрабатывать
        """
        # Проверяем существование пользователя
        user = self.users.get(user_id)
        if not user or not user["is_active"]:
            return False

        # Сбрасываем дневные лимиты если нужно
        await self._reset_daily_limits_if_needed(user_id)

        # Проверяем дневной лимит
        usage = self.user_usage.get(user_id, {})
        daily_generations = usage.get("daily_generations", 0)

        # Если у пользователя есть активная подписка, проверяем лимит
        if user.get("subscription", {}).get("active", False):
            return daily_generations < settings.DAILY_GENERATION_LIMIT
        else:
            # Без подписки - только несколько бесплатных обработок
            return daily_generations < 3  # Бесплатный лимит

    async def increment_processing_count(self, user_id: str):
        """
        Увеличение счетчика обработок пользователя

        Args:
            user_id: ID пользователя
        """
        if user_id not in self.user_usage:
            self.user_usage[user_id] = {
                "daily_generations": 0,
                "monthly_generations": 0,
                "total_generations": 0,
                "last_processing_date": None,
                "daily_reset_date": datetime.now().date(),
                "monthly_reset_date": datetime.now().replace(day=1).date(),
            }

        usage = self.user_usage[user_id]

        # Увеличиваем счетчики
        usage["daily_generations"] += 1
        usage["monthly_generations"] += 1
        usage["total_generations"] += 1
        usage["last_processing_date"] = datetime.now()

        self.logger.info(f"Увеличен счетчик обработок для пользователя {user_id}")

    async def activate_subscription(
        self, user_id: str, plan: str, duration_days: int = 30
    ) -> bool:
        """
        Активация подписки пользователя

        Args:
            user_id: ID пользователя
            plan: План подписки
            duration_days: Длительность в днях

        Returns:
            True если успешно
        """
        user = self.users.get(user_id)
        if not user:
            return False

        now = datetime.now()
        ends_at = now + timedelta(days=duration_days)

        user["subscription"] = {
            "active": True,
            "plan": plan,
            "started_at": now,
            "ends_at": ends_at,
            "auto_renew": True,
        }

        user["updated_at"] = now

        self.logger.info(f"Активирована подписка для пользователя {user_id}")

        return True

    async def deactivate_subscription(self, user_id: str) -> bool:
        """
        Деактивация подписки пользователя

        Args:
            user_id: ID пользователя

        Returns:
            True если успешно
        """
        user = self.users.get(user_id)
        if not user:
            return False

        user["subscription"]["active"] = False
        user["subscription"]["auto_renew"] = False
        user["updated_at"] = datetime.now()

        self.logger.info(f"Деактивирована подписка для пользователя {user_id}")

        return True

    async def check_health(self) -> bool:
        """
        Проверка здоровья сервиса

        Returns:
            True если сервис здоров
        """
        try:
            # Проверяем, что сервис инициализирован
            if not self.users:
                self.logger.warning("Сервис пользователей не инициализирован")
                return True  # Это нормально для начала работы

            # Проверяем целостность данных
            for user_id, user in self.users.items():
                if not all(
                    key in user for key in ["id", "email", "username", "password_hash"]
                ):
                    self.logger.warning(f"Некорректные данные пользователя: {user_id}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Ошибка при проверке здоровья: {str(e)}")
            return False

    async def _create_tokens(self, user_id: str) -> TokenResponse:
        """
        Создание токенов доступа

        Args:
            user_id: ID пользователя

        Returns:
            Токены доступа
        """
        # Создаем ID сессии
        session_id = str(uuid.uuid4())
        refresh_token_id = str(uuid.uuid4())

        now = datetime.now()
        access_expires = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Создаем payload для access токена
        access_payload = {
            "sub": user_id,
            "sid": session_id,
            "exp": int(access_expires.timestamp()),
            "iat": int(now.timestamp()),
            "type": "access",
        }

        # Создаем payload для refresh токена
        refresh_payload = {
            "sub": user_id,
            "jti": refresh_token_id,
            "exp": int(refresh_expires.timestamp()),
            "iat": int(now.timestamp()),
            "type": "refresh",
        }

        # Создаем токены
        access_token = jwt.encode(
            access_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        refresh_token = jwt.encode(
            refresh_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        # Сохраняем сессию
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": now,
            "last_activity": now,
            "revoked": False,
        }

        # Сохраняем refresh токен
        self.refresh_tokens[refresh_token_id] = {
            "user_id": user_id,
            "created_at": now,
            "revoked": False,
            "used": False,
            "used_at": None,
        }

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def _hash_password(self, password: str) -> str:
        """
        Хеширование пароля

        Args:
            password: Пароль

        Returns:
            Хеш пароля
        """
        # Используем salt для безопасности
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, 100000, dklen=128
        )
        return salt.hex() + key.hex()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        Проверка пароля

        Args:
            password: Пароль для проверки
            password_hash: Хеш пароля

        Returns:
            True если пароль верный
        """
        try:
            # Извлекаем salt и key из хеша
            salt = bytes.fromhex(password_hash[:64])
            stored_key = bytes.fromhex(password_hash[64:])

            # Вычисляем хеш для проверяемого пароля
            computed_key = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, 100000, dklen=128
            )

            # Сравниваем
            return secrets.compare_digest(stored_key, computed_key)

        except Exception:
            return False

    async def _reset_daily_limits_if_needed(self, user_id: str):
        """
        Сброс дневных лимитов если наступил новый день

        Args:
            user_id: ID пользователя
        """
        if user_id not in self.user_usage:
            return

        usage = self.user_usage[user_id]
        today = datetime.now().date()

        # Сбрасываем дневные лимиты если наступил новый день
        if usage.get("daily_reset_date") != today:
            usage["daily_generations"] = 0
            usage["daily_reset_date"] = today
            self.logger.debug(f"Сброшены дневные лимиты для пользователя {user_id}")

        # Сбрасываем месячные лимиты если наступил новый месяц
        current_month = today.replace(day=1)
        if usage.get("monthly_reset_date") != current_month:
            usage["monthly_generations"] = 0
            usage["monthly_reset_date"] = current_month
            self.logger.debug(f"Сброшены месячные лимиты для пользователя {user_id}")
