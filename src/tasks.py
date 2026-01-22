"""
Задачи Celery для асинхронной обработки аудио
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from celery import Celery, Task
from celery.schedules import crontab
from pydantic import ValidationError

from config.settings import settings
from services.audio_processor import AudioProcessor
from services.user_manager import UserManager
from utils.audio_utils import (
    convert_audio_format,
    get_audio_info,
    load_audio_file,
    normalize_audio,
    save_audio_file,
)
from utils.storage import StorageManager
from utils.validators import validate_audio_file

# Настройка логирования
logger = logging.getLogger(__name__)

# Создание экземпляра Celery
celery_app = Celery(
    "stereobrother_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Конфигурация Celery
celery_app.conf.update(
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    beat_schedule={
        # Очистка временных файлов каждый час
        "cleanup-temp-files": {
            "task": "src.tasks.cleanup_temp_files",
            "schedule": crontab(minute=0),  # Каждый час
        },
        # Сброс дневных лимитов в полночь
        "reset-daily-limits": {
            "task": "src.tasks.reset_daily_limits",
            "schedule": crontab(hour=0, minute=0),  # Каждый день в 00:00
        },
        # Удаление старых обработанных файлов
        "cleanup-old-files": {
            "task": "src.tasks.cleanup_old_processed_files",
            "schedule": crontab(hour=2, minute=0),  # Каждый день в 02:00
        },
        # Проверка подписок
        "check-subscriptions": {
            "task": "src.tasks.check_subscriptions",
            "schedule": crontab(hour=3, minute=0),  # Каждый день в 03:00
        },
        # Отправка статистики
        "send-daily-stats": {
            "task": "src.tasks.send_daily_statistics",
            "schedule": crontab(hour=9, minute=0),  # Каждый день в 09:00
        },
    },
)

# Инициализация сервисов
audio_processor = AudioProcessor()
user_manager = UserManager()
storage_manager = StorageManager()


class BaseTask(Task):
    """
    Базовая задача Celery с обработкой ошибок
    """

    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Обработка ошибок выполнения задачи
        """
        logger.error(f"Задача {task_id} завершилась с ошибкой: {exc}")
        logger.error(f"Аргументы: {args}, {kwargs}")
        logger.error(f"Информация об ошибке: {einfo}")

    def on_success(self, retval, task_id, args, kwargs):
        """
        Обработка успешного выполнения задачи
        """
        logger.info(f"Задача {task_id} успешно выполнена")
        logger.debug(f"Результат: {retval}")


@celery_app.task(base=BaseTask, bind=True, name="process_audio_upload")
def process_audio_upload(
    self,
    task_id: str,
    user_id: str,
    file_path: str,
    original_filename: str,
) -> Dict:
    """
    Задача обработки загруженного аудио файла

    Args:
        task_id: ID задачи
        user_id: ID пользователя
        file_path: Путь к файлу
        original_filename: Оригинальное имя файла

    Returns:
        Результат обработки
    """
    try:
        logger.info(f"Начало обработки загрузки аудио: {task_id}")

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 10})

        # Валидируем файл
        validation_result = validate_audio_file(
            file_path=file_path,
            max_duration=settings.max_file_duration_seconds,
            allowed_formats=settings.SUPPORTED_INPUT_FORMATS,
        )

        if not validation_result["valid"]:
            raise ValueError(f"Файл не прошел валидацию: {validation_result['error']}")

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 30})

        # Получаем информацию об аудио файле
        audio_info = get_audio_info(file_path)

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 50})

        # Конвертируем в стандартный формат если нужно
        if audio_info["format"] not in ["WAV", "wav"]:
            converted_path = os.path.join(
                settings.TEMP_DIR, f"converted_{task_id}.wav"
            )
            convert_audio_format(
                input_path=file_path,
                output_path=converted_path,
                output_format="wav",
                sample_rate=settings.AUDIO_SAMPLE_RATE,
                channels=settings.AUDIO_CHANNELS,
            )
            processed_path = converted_path
        else:
            processed_path = file_path

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 70})

        # Нормализуем аудио
        audio_data, sample_rate = load_audio_file(processed_path)
        normalized_audio = normalize_audio(audio_data, target_level=-1.0)

        # Сохраняем нормализованную версию
        normalized_path = os.path.join(settings.TEMP_DIR, f"normalized_{task_id}.wav")
        save_audio_file(normalized_path, normalized_audio, sample_rate)

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 90})

        # Загружаем в хранилище
        storage_filename = f"original_{task_id}.wav"
        download_url = storage_manager.upload_file(normalized_path, storage_filename)

        # Очищаем временные файлы
        if processed_path != file_path and os.path.exists(processed_path):
            os.remove(processed_path)
        if os.path.exists(normalized_path):
            os.remove(normalized_path)

        result = {
            "task_id": task_id,
            "user_id": user_id,
            "status": "completed",
            "audio_info": audio_info,
            "download_url": download_url,
            "processed_at": datetime.now().isoformat(),
        }

        logger.info(f"Загрузка аудио обработана: {task_id}")
        return result

    except Exception as e:
        logger.error(f"Ошибка при обработке загрузки аудио {task_id}: {str(e)}")
        raise


@celery_app.task(base=BaseTask, bind=True, name="enhance_audio_task")
def enhance_audio_task(
    self,
    task_id: str,
    user_id: str,
    input_file_path: str,
    mode: str,
    instrument: Optional[str] = None,
) -> Dict:
    """
    Задача улучшения качества аудио

    Args:
        task_id: ID задачи
        user_id: ID пользователя
        input_file_path: Путь к входному файлу
        mode: Режим улучшения
        instrument: Инструмент для улучшения

    Returns:
        Результат обработки
    """
    try:
        logger.info(f"Начало улучшения аудио: {task_id}, режим: {mode}")

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 10})

        # Загружаем аудио
        audio_data, sample_rate = load_audio_file(input_file_path)

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 30})

        # Применяем улучшение
        enhanced_audio = audio_processor._enhance_full_mix(audio_data, sample_rate)

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 70})

        # Сохраняем результат
        output_filename = f"enhanced_{mode}_{task_id}.wav"
        output_path = os.path.join(settings.TEMP_DIR, output_filename)
        save_audio_file(output_path, enhanced_audio, sample_rate)

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 90})

        # Загружаем в хранилище
        download_url = storage_manager.upload_file(output_path, output_filename)

        # Очищаем временный файл
        if os.path.exists(output_path):
            os.remove(output_path)

        result = {
            "task_id": task_id,
            "user_id": user_id,
            "status": "completed",
            "processing_type": "enhancement",
            "mode": mode,
            "instrument": instrument,
            "download_url": download_url,
            "processed_at": datetime.now().isoformat(),
        }

        logger.info(f"Улучшение аудио завершено: {task_id}")
        return result

    except Exception as e:
        logger.error(f"Ошибка при улучшении аудио {task_id}: {str(e)}")
        raise


@celery_app.task(base=BaseTask, bind=True, name="denoise_audio_task")
def denoise_audio_task(
    self,
    task_id: str,
    user_id: str,
    input_file_path: str,
    noise_types: List[str],
    intensity: float = 0.5,
) -> Dict:
    """
    Задача очистки аудио от шумов

    Args:
        task_id: ID задачи
        user_id: ID пользователя
        input_file_path: Путь к входному файлу
        noise_types: Типы шумов для удаления
        intensity: Интенсивность очистки

    Returns:
        Результат обработки
    """
    try:
        logger.info(f"Начало очистки аудио: {task_id}, типы шумов: {noise_types}")

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 10})

        # Загружаем аудио
        audio_data, sample_rate = load_audio_file(input_file_path)

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 30})

        # Применяем денойзинг
        denoised_audio = audio_processor._apply_denoising(
            audio_data, sample_rate, noise_types, intensity
        )

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 70})

        # Сохраняем результат
        output_filename = f"denoised_{task_id}.wav"
        output_path = os.path.join(settings.TEMP_DIR, output_filename)
        save_audio_file(output_path, denoised_audio, sample_rate)

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 90})

        # Загружаем в хранилище
        download_url = storage_manager.upload_file(output_path, output_filename)

        # Очищаем временный файл
        if os.path.exists(output_path):
            os.remove(output_path)

        result = {
            "task_id": task_id,
            "user_id": user_id,
            "status": "completed",
            "processing_type": "denoise",
            "noise_types": noise_types,
            "intensity": intensity,
            "download_url": download_url,
            "processed_at": datetime.now().isoformat(),
        }

        logger.info(f"Очистка аудио завершена: {task_id}")
        return result

    except Exception as e:
        logger.error(f"Ошибка при очистке аудио {task_id}: {str(e)}")
        raise


@celery_app.task(base=BaseTask, bind=True, name="separate_stems_task")
def separate_stems_task(
    self,
    task_id: str,
    user_id: str,
    input_file_path: str,
    configuration: str,
) -> Dict:
    """
    Задача разделения аудио на дорожки

    Args:
        task_id: ID задачи
        user_id: ID пользователя
        input_file_path: Путь к входному файлу
        configuration: Конфигурация разделения

    Returns:
        Результат обработки
    """
    try:
        logger.info(f"Начало разделения аудио: {task_id}, конфигурация: {configuration}")

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 10})

        # Загружаем аудио
        audio_data, sample_rate = load_audio_file(input_file_path)

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 30})

        # Разделяем на дорожки
        stems = audio_processor._separate_audio_stems(
            audio_data, sample_rate, configuration
        )

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 50})

        # Сохраняем результаты
        stem_results = {}
        download_urls = {}

        for i, (stem_name, stem_audio) in enumerate(stems.items()):
            # Обновляем прогресс для каждой дорожки
            progress = 50 + (i * 40 / len(stems))
            self.update_state(state="PROGRESS", meta={"progress": progress})

            # Сохраняем дорожку
            output_filename = f"{stem_name}_{task_id}.wav"
            output_path = os.path.join(settings.TEMP_DIR, output_filename)
            save_audio_file(output_path, stem_audio, sample_rate)

            # Загружаем в хранилище
            download_url = storage_manager.upload_file(output_path, output_filename)
            download_urls[stem_name] = download_url

            # Очищаем временный файл
            if os.path.exists(output_path):
                os.remove(output_path)

            stem_results[stem_name] = {
                "filename": output_filename,
                "size": len(stem_audio.tobytes()),
            }

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 90})

        result = {
            "task_id": task_id,
            "user_id": user_id,
            "status": "completed",
            "processing_type": "stem_separation",
            "configuration": configuration,
            "stems": stem_results,
            "download_urls": download_urls,
            "processed_at": datetime.now().isoformat(),
        }

        logger.info(f"Разделение аудио завершено: {task_id}")
        return result

    except Exception as e:
        logger.error(f"Ошибка при разделении аудио {task_id}: {str(e)}")
        raise


@celery_app.task(base=BaseTask, bind=True, name="master_audio_task")
def master_audio_task(
    self,
    task_id: str,
    user_id: str,
    input_file_path: str,
    preset: str,
    output_format: str,
    target_loudness: float = -14.0,
) -> Dict:
    """
    Задача мастеринга аудио

    Args:
        task_id: ID задачи
        user_id: ID пользователя
        input_file_path: Путь к входному файлу
        preset: Пресет мастеринга
        output_format: Формат вывода
        target_loudness: Целевая громкость

    Returns:
        Результат обработки
    """
    try:
        logger.info(f"Начало мастеринга аудио: {task_id}, пресет: {preset}")

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 10})

        # Загружаем аудио
        audio_data, sample_rate = load_audio_file(input_file_path)

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 30})

        # Применяем мастеринг
        mastered_audio = audio_processor._apply_mastering(
            audio_data, sample_rate, preset, target_loudness
        )

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 60})

        # Определяем расширение файла
        ext = "mp3" if output_format == "mp3" else "wav"

        # Сохраняем результат
        output_filename = f"mastered_{preset}_{task_id}.{ext}"
        output_path = os.path.join(settings.TEMP_DIR, output_filename)
        save_audio_file(output_path, mastered_audio, sample_rate)

        # Обновляем прогресс
        self.update_state(state="PROGRESS", meta={"progress": 90})

        # Загружаем в хранилище
        download_url = storage_manager.upload_file(output_path, output_filename)

        # Очищаем временный файл
        if os.path.exists(output_path):
            os.remove(output_path)

        result = {
            "task_id": task_id,
            "user_id": user_id,
            "status": "completed",
            "processing_type": "mastering",
            "preset": preset,
            "output_format": output_format,
            "target_loudness": target_loudness,
            "download_url": download_url,
            "processed_at": datetime
