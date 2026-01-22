"""
Конфигурационные настройки бота для ИИ-обработки аудио
"""

import os
from datetime import timedelta
from typing import Dict, List, Optional

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Основные настройки приложения"""

    # Настройки приложения
    APP_NAME: str = "StereoBrother Audio AI Bot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Настройки сервера
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Настройки базы данных
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/stereobrother_db",
        env="DATABASE_URL",
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # Настройки Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_POOL_SIZE: int = 10

    # Настройки хранилища файлов
    STORAGE_TYPE: str = "local"  # local, s3, minio
    LOCAL_STORAGE_PATH: str = "./storage"
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None
    S3_REGION: Optional[str] = None

    # Настройки безопасности
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production", env="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Настройки CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Настройки лимитов (из технического задания)
    MAX_FILE_DURATION_MINUTES: int = 10  # Максимальная длительность файла
    DAILY_GENERATION_LIMIT: int = 100  # Дневной лимит генераций
    SUBSCRIPTION_PRICE_RUB: int = 500  # Стоимость подписки

    # Поддерживаемые форматы файлов
    SUPPORTED_INPUT_FORMATS: List[str] = [
        "mp3",
        "wav",
        "m4a",
        "ogg",
        "flac",
        "aac",
        "wma",
    ]
    SUPPORTED_OUTPUT_FORMATS: List[str] = ["wav", "mp3"]

    # Настройки обработки аудио
    AUDIO_SAMPLE_RATE: int = 44100
    AUDIO_CHANNELS: int = 2
    AUDIO_BIT_DEPTH: int = 16

    # Настройки моделей ИИ
    AI_MODELS_PATH: str = "./models"

    # Модели для различных задач
    DENOISE_MODEL: str = "demucs"
    STEM_SEPARATION_MODEL: str = "demucs"
    ENHANCEMENT_MODEL: str = "audio_super_resolution"
    MASTERING_MODEL: str = "ai_mastering"

    # Конфигурация разделения дорожек
    STEM_SEPARATION_TRACKS: Dict[str, List[str]] = {
        "basic": ["vocals", "drums", "bass", "other"],
        "advanced": ["vocals", "drums", "bass", "guitar", "piano", "other"],
    }

    # Пресеты мастеринга
    MASTERING_PRESETS: Dict[str, Dict[str, float]] = {
        "podcast": {
            "name": "Мастеринг подкаста",
            "description": "Акцент на четкость речи",
            "eq_high_pass": 80.0,
            "eq_low_pass": 16000.0,
            "compression_ratio": 2.0,
            "limiter_threshold": -1.0,
        },
        "song": {
            "name": "Мастеринг песни",
            "description": "Музыкальный баланс, плотность",
            "eq_high_pass": 40.0,
            "eq_low_pass": 20000.0,
            "compression_ratio": 3.0,
            "limiter_threshold": -0.5,
        },
        "advertisement": {
            "name": "Мастеринг рекламы",
            "description": "Громкость, яркость, 'радийный' звук",
            "eq_high_pass": 100.0,
            "eq_low_pass": 15000.0,
            "compression_ratio": 4.0,
            "limiter_threshold": 0.0,
        },
    }

    # Настройки инструментов улучшения
    ENHANCEMENT_MODES: Dict[str, List[str]] = {
        "full_mix": ["Улучшение полного микса"],
        "individual_tracks": ["drums", "guitars", "bass", "strings", "piano", "vocals"],
    }

    # Настройки временных файлов
    TEMP_DIR: str = "./temp"
    TEMP_FILE_RETENTION_HOURS: int = 24
    PROCESSED_FILE_RETENTION_DAYS: int = 30

    # Настройки очередей задач
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1", env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND"
    )
    CELERY_TASK_TIME_LIMIT: int = 1800  # 30 минут
    CELERY_TASK_SOFT_TIME_LIMIT: int = 1500  # 25 минут

    # Настройки логирования
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "./logs/app.log"

    # Настройки мониторинга
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    HEALTH_CHECK_PATH: str = "/health"

    # Настройки платежной системы
    PAYMENT_PROVIDER: str = "yookassa"  # yookassa, cloudpayments
    YOOKASSA_SHOP_ID: Optional[str] = None
    YOOKASSA_SECRET_KEY: Optional[str] = None
    CLOUDPAYMENTS_PUBLIC_ID: Optional[str] = None
    CLOUDPAYMENTS_API_SECRET: Optional[str] = None

    # Настройки уведомлений
    EMAIL_ENABLED: bool = False
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # Настройки кэширования
    CACHE_TTL_SECONDS: int = 300  # 5 минут
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD_SECONDS: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("LOCAL_STORAGE_PATH", "TEMP_DIR", "AI_MODELS_PATH", "LOG_FILE")
    def ensure_directories_exist(cls, v):
        """Создает директории, если они не существуют"""
        os.makedirs(v, exist_ok=True)
        return v

    @validator("SUPPORTED_INPUT_FORMATS", "SUPPORTED_OUTPUT_FORMATS")
    def normalize_formats(cls, v):
        """Приводит форматы к нижнему регистру"""
        return [fmt.lower() for fmt in v]

    @property
    def max_file_duration_seconds(self) -> int:
        """Возвращает максимальную длительность файла в секундах"""
        return self.MAX_FILE_DURATION_MINUTES * 60

    @property
    def database_config(self) -> Dict:
        """Возвращает конфигурацию базы данных"""
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "echo": self.DEBUG,
        }

    @property
    def redis_config(self) -> Dict:
        """Возвращает конфигурацию Redis"""
        return {"url": self.REDIS_URL, "pool_size": self.REDIS_POOL_SIZE}

    @property
    def storage_config(self) -> Dict:
        """Возвращает конфигурацию хранилища"""
        config = {"type": self.STORAGE_TYPE, "local_path": self.LOCAL_STORAGE_PATH}

        if self.STORAGE_TYPE == "s3":
            config.update(
                {
                    "endpoint_url": self.S3_ENDPOINT_URL,
                    "access_key": self.S3_ACCESS_KEY,
                    "secret_key": self.S3_SECRET_KEY,
                    "bucket_name": self.S3_BUCKET_NAME,
                    "region": self.S3_REGION,
                }
            )

        return config

    @property
    def celery_config(self) -> Dict:
        """Возвращает конфигурацию Celery"""
        return {
            "broker_url": self.CELERY_BROKER_URL,
            "result_backend": self.CELERY_RESULT_BACKEND,
            "task_time_limit": self.CELERY_TASK_TIME_LIMIT,
            "task_soft_time_limit": self.CELERY_TASK_SOFT_TIME_LIMIT,
            "worker_prefetch_multiplier": 1,
            "task_acks_late": True,
        }

    @property
    def payment_config(self) -> Dict:
        """Возвращает конфигурацию платежной системы"""
        config = {"provider": self.PAYMENT_PROVIDER}

        if self.PAYMENT_PROVIDER == "yookassa":
            config.update(
                {
                    "shop_id": self.YOOKASSA_SHOP_ID,
                    "secret_key": self.YOOKASSA_SECRET_KEY,
                }
            )
        elif self.PAYMENT_PROVIDER == "cloudpayments":
            config.update(
                {
                    "public_id": self.CLOUDPAYMENTS_PUBLIC_ID,
                    "api_secret": self.CLOUDPAYMENTS_API_SECRET,
                }
            )

        return config

    @property
    def is_production(self) -> bool:
        """Проверяет, является ли среда production"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Проверяет, является ли среда development"""
        return self.ENVIRONMENT.lower() == "development"


# Создаем экземпляр настроек
settings = Settings()

# Экспортируем настройки для удобного использования
__all__ = ["settings"]
