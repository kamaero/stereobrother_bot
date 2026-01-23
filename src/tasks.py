"""
Minimal Celery tasks for testing purposes.
This is a simplified version of the tasks module.
"""

import logging
from datetime import datetime

from celery import Celery

from config.settings import settings

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
)


# Базовый класс задачи
class BaseTask(celery_app.Task):
    """Базовый класс для всех задач Celery."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Обработчик неудачи задачи."""
        logger.error(f"Task {task_id} failed: {exc}")

    def on_success(self, retval, task_id, args, kwargs):
        """Обработчик успешного выполнения задачи."""
        logger.info(f"Task {task_id} completed successfully")


# Задачи обработки аудио (заглушки)
@celery_app.task(base=BaseTask, bind=True)
def process_audio_upload(self, audio_id: str, user_id: str):
    """Задача обработки загрузки аудио."""
    logger.info(f"Processing audio upload: {audio_id} for user {user_id}")

    # Имитация обработки
    self.update_state(state="PROGRESS", meta={"progress": 50})

    # Возвращаем результат
    return {
        "task_id": self.request.id,
        "audio_id": audio_id,
        "user_id": user_id,
        "status": "completed",
        "processed_at": datetime.now().isoformat(),
    }


@celery_app.task(base=BaseTask, bind=True)
def enhance_audio_task(self, audio_id: str, user_id: str, parameters: dict):
    """Задача улучшения качества аудио."""
    logger.info(f"Enhancing audio: {audio_id} for user {user_id}")

    # Имитация обработки
    for i in range(1, 6):
        self.update_state(state="PROGRESS", meta={"progress": i * 20})

    return {
        "task_id": self.request.id,
        "audio_id": audio_id,
        "user_id": user_id,
        "status": "completed",
        "processing_type": "enhancement",
        "parameters": parameters,
        "processed_at": datetime.now().isoformat(),
    }


@celery_app.task(base=BaseTask, bind=True)
def denoise_audio_task(self, audio_id: str, user_id: str, parameters: dict):
    """Задача удаления шума из аудио."""
    logger.info(f"Denoising audio: {audio_id} for user {user_id}")

    # Имитация обработки
    for i in range(1, 6):
        self.update_state(state="PROGRESS", meta={"progress": i * 20})

    return {
        "task_id": self.request.id,
        "audio_id": audio_id,
        "user_id": user_id,
        "status": "completed",
        "processing_type": "denoising",
        "parameters": parameters,
        "processed_at": datetime.now().isoformat(),
    }


@celery_app.task(base=BaseTask, bind=True)
def separate_stems_task(self, audio_id: str, user_id: str, parameters: dict):
    """Задача разделения аудио на дорожки."""
    logger.info(f"Separating stems: {audio_id} for user {user_id}")

    # Имитация обработки
    for i in range(1, 6):
        self.update_state(state="PROGRESS", meta={"progress": i * 20})

    return {
        "task_id": self.request.id,
        "audio_id": audio_id,
        "user_id": user_id,
        "status": "completed",
        "processing_type": "stem_separation",
        "parameters": parameters,
        "processed_at": datetime.now().isoformat(),
    }


@celery_app.task(base=BaseTask, bind=True)
def master_audio_task(self, audio_id: str, user_id: str, parameters: dict):
    """Задача мастеринга аудио."""
    logger.info(f"Mastering audio: {audio_id} for user {user_id}")

    # Имитация обработки
    for i in range(1, 6):
        self.update_state(state="PROGRESS", meta={"progress": i * 20})

    return {
        "task_id": self.request.id,
        "audio_id": audio_id,
        "user_id": user_id,
        "status": "completed",
        "processing_type": "mastering",
        "parameters": parameters,
        "processed_at": datetime.now().isoformat(),
    }


# Периодические задачи (заглушки)
@celery_app.task(base=BaseTask)
def cleanup_temp_files():
    """Очистка временных файлов."""
    logger.info("Cleaning up temporary files")
    return {"cleaned": 0, "message": "No files to clean"}


@celery_app.task(base=BaseTask)
def update_usage_statistics():
    """Обновление статистики использования."""
    logger.info("Updating usage statistics")
    return {"updated": True, "timestamp": datetime.now().isoformat()}


# Конфигурация периодических задач
celery_app.conf.beat_schedule = {
    "cleanup-temp-files-every-hour": {
        "task": "src.tasks_minimal.cleanup_temp_files",
        "schedule": 3600.0,  # каждый час
    },
    "update-statistics-daily": {
        "task": "src.tasks_minimal.update_usage_statistics",
        "schedule": 86400.0,  # каждый день
    },
}
