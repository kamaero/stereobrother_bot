"""
Утилиты для работы с хранилищем файлов
"""

import asyncio
import hashlib
import logging
import mimetypes
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Dict, Optional, Tuple, Union
from urllib.parse import urljoin

import aiofiles
import aiohttp
from botocore.exceptions import ClientError

from config.settings import settings

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Менеджер хранилища файлов с поддержкой локального и S3 хранилищ
    """

    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.config = settings.storage_config
        self.s3_client = None
        self.session = None

        # Инициализируем хранилище в зависимости от типа
        if self.storage_type == "s3":
            self._init_s3_client()
        elif self.storage_type == "local":
            self._init_local_storage()
        else:
            raise ValueError(f"Неподдерживаемый тип хранилища: {self.storage_type}")

    def _init_s3_client(self):
        """
        Инициализация S3 клиента
        """
        try:
            import boto3
            from botocore.config import Config

            s3_config = Config(
                region_name=self.config.get("region"),
                signature_version="s3v4",
                max_pool_connections=50,
            )

            self.s3_client = boto3.client(
                "s3",
                endpoint_url=self.config.get("endpoint_url"),
                aws_access_key_id=self.config.get("access_key"),
                aws_secret_access_key=self.config.get("secret_key"),
                config=s3_config,
            )

            # Проверяем подключение
            self.s3_client.head_bucket(Bucket=self.config.get("bucket_name"))
            logger.info("S3 клиент инициализирован")

        except ImportError:
            logger.error("boto3 не установлен. Установите: pip install boto3")
            raise
        except Exception as e:
            logger.error(f"Ошибка при инициализации S3 клиента: {str(e)}")
            raise

    def _init_local_storage(self):
        """
        Инициализация локального хранилища
        """
        local_path = self.config.get("local_path", "./storage")
        os.makedirs(local_path, exist_ok=True)

        # Создаем поддиректории
        subdirs = ["uploads", "processed", "temp", "exports"]
        for subdir in subdirs:
            os.makedirs(os.path.join(local_path, subdir), exist_ok=True)

        logger.info(f"Локальное хранилище инициализировано: {local_path}")

    async def upload_file(
        self,
        file_path: str,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict] = None,
        public: bool = False,
    ) -> str:
        """
        Загрузка файла в хранилище

        Args:
            file_path: Путь к файлу на локальной файловой системе
            filename: Имя файла в хранилище (если None, используется оригинальное имя)
            content_type: MIME тип файла
            metadata: Дополнительные метаданные
            public: Делать ли файл публичным

        Returns:
            URL для доступа к файлу
        """
        try:
            if not os.path.exists(file_path):
                raise ValueError(f"Файл не существует: {file_path}")

            # Определяем имя файла
            if not filename:
                filename = os.path.basename(file_path)

            # Определяем MIME тип
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = "application/octet-stream"

            # Читаем файл
            async with aiofiles.open(file_path, "rb") as f:
                file_data = await f.read()

            # Загружаем в хранилище
            if self.storage_type == "s3":
                url = await self._upload_to_s3(
                    file_data, filename, content_type, metadata, public
                )
            else:
                url = await self._upload_to_local(
                    file_data, filename, content_type, metadata
                )

            logger.info(f"Файл загружен в хранилище: {filename}")
            return url

        except Exception as e:
            logger.error(f"Ошибка при загрузке файла {file_path}: {str(e)}")
            raise

    async def download_file(
        self, filename: str, destination_path: str
    ) -> str:
        """
        Скачивание файла из хранилища

        Args:
            filename: Имя файла в хранилище
            destination_path: Путь для сохранения файла

        Returns:
            Путь к скачанному файлу
        """
        try:
            if self.storage_type == "s3":
                await self._download_from_s3(filename, destination_path)
            else:
                await self._download_from_local(filename, destination_path)

            logger.info(f"Файл скачан из хранилища: {filename}")
            return destination_path

        except Exception as e:
            logger.error(f"Ошибка при скачивании файла {filename}: {str(e)}")
            raise

    async def delete_file(self, filename: str) -> bool:
        """
        Удаление файла из хранилища

        Args:
            filename: Имя файла в хранилище

        Returns:
            True если файл удален
        """
        try:
            if self.storage_type == "s3":
                success = await self._delete_from_s3(filename)
            else:
                success = await self._delete_from_local(filename)

            if success:
                logger.info(f"Файл удален из хранилища: {filename}")
            else:
                logger.warning(f"Файл не найден в хранилище: {filename}")

            return success

        except Exception as e:
            logger.error(f"Ошибка при удалении файла {filename}: {str(e)}")
            raise

    async def get_file_url(
        self, filename: str, expires_in: int = 3600
    ) -> str:
        """
        Получение URL для доступа к файлу

        Args:
            filename: Имя файла в хранилище
            expires_in: Время жизни ссылки в секундах

        Returns:
            URL для доступа к файлу
        """
        try:
            if self.storage_type == "s3":
                url = await self._get_s3_url(filename, expires_in)
            else:
                url = await self._get_local_url(filename)

            return url

        except Exception as e:
            logger.error(f"Ошибка при получении URL файла {filename}: {str(e)}")
            raise

    async def file_exists(self, filename: str) -> bool:
        """
        Проверка существования файла в хранилище

        Args:
            filename: Имя файла в хранилище

        Returns:
            True если файл существует
        """
        try:
            if self.storage_type == "s3":
                exists = await self._s3_file_exists(filename)
            else:
                exists = await self._local_file_exists(filename)

            return exists

        except Exception as e:
            logger.error(f"Ошибка при проверке существования файла {filename}: {str(e)}")
            return False

    async def get_file_info(self, filename: str) -> Optional[Dict]:
        """
        Получение информации о файле

        Args:
            filename: Имя файла в хранилище

        Returns:
            Информация о файле или None
        """
        try:
            if self.storage_type == "s3":
                info = await self._get_s3_file_info(filename)
            else:
                info = await self._get_local_file_info(filename)

            return info

        except Exception as e:
            logger.error(f"Ошибка при получении информации о файле {filename}: {str(e)}")
            return None

    async def list_files(
        self, prefix: str = "", limit: int = 100, offset: int = 0
    ) -> Dict:
        """
        Список файлов в хранилище

        Args:
            prefix: Префикс для фильтрации
            limit: Максимальное количество файлов
            offset: Смещение

        Returns:
            Словарь с информацией о файлах
        """
        try:
            if self.storage_type == "s3":
                files = await self._list_s3_files(prefix, limit, offset)
            else:
                files = await self._list_local_files(prefix, limit, offset)

            return files

        except Exception as e:
            logger.error(f"Ошибка при получении списка файлов: {str(e)}")
            return {"files": [], "total": 0}

    async def cleanup_old_files(
        self, days: int = 30, prefix: str = "temp/"
    ) -> int:
        """
        Очистка старых файлов

        Args:
            days: Удалять файлы старше указанного количества дней
            prefix: Префикс для фильтрации файлов

        Returns:
            Количество удаленных файлов
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0

            if self.storage_type == "s3":
                deleted_count = await self._cleanup_s3_files(cutoff_date, prefix)
            else:
                deleted_count = await self._cleanup_local_files(cutoff_date, prefix)

            logger.info(f"Удалено {deleted_count} старых файлов")
            return deleted_count

        except Exception as e:
            logger.error(f"Ошибка при очистке старых файлов: {str(e)}")
            return 0

    async def check_health(self) -> bool:
        """
        Проверка здоровья хранилища

        Returns:
            True если хранилище доступно
        """
        try:
            if self.storage_type == "s3":
                healthy = await self._check_s3_health()
            else:
                healthy = await self._check_local_health()

            return healthy

        except Exception as e:
            logger.error(f"Ошибка при проверке здоровья хранилища: {str(e)}")
            return False

    # S3 методы
    async def _upload_to_s3(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        metadata: Optional[Dict],
        public: bool,
    ) -> str:
        """
        Загрузка файла в S3
        """
        bucket_name = self.config.get("bucket_name")
        extra_args = {
            "ContentType": content_type,
            "Metadata": metadata or {},
        }

        if public:
            extra_args["ACL"] = "public-read"

        # Загружаем файл
        self.s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=file_data,
            **extra_args,
        )

        # Генерируем URL
        if public:
            url = f"{self.config.get('endpoint_url')}/{bucket_name}/{filename}"
        else:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": filename},
                ExpiresIn=3600,
            )

        return url

    async def _download_from_s3(self, filename: str, destination_path: str):
        """
        Скачивание файла из S3
        """
        bucket_name = self.config.get("bucket_name")

        # Скачиваем файл
        self.s3_client.download_file(
            bucket_name, filename, destination_path
        )

    async def _delete_from_s3(self, filename: str) -> bool:
        """
        Удаление файла из S3
        """
        bucket_name = self.config.get("bucket_name")

        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=filename)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    async def _get_s3_url(self, filename: str, expires_in: int) -> str:
        """
        Получение URL файла из S3
        """
        bucket_name = self.config.get("bucket_name")

        url = self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": filename},
            ExpiresIn=expires_in,
        )

        return url

    async def _s3_file_exists(self, filename: str) -> bool:
        """
        Проверка существования файла в S3
        """
        bucket_name = self.config.get("bucket_name")

        try:
            self.s3_client.head_object(Bucket=bucket_name, Key=filename)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    async def _get_s3_file_info(self, filename: str) -> Optional[Dict]:
        """
        Получение информации о файле в S3
        """
        bucket_name = self.config.get("bucket_name")

        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=filename)
            return {
                "filename": filename,
                "size": response["ContentLength"],
                "content_type": response.get("ContentType"),
                "last_modified": response["LastModified"],
                "metadata": response.get("Metadata", {}),
                "etag": response["ETag"],
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return None
            raise

    async def _list_s3_files(
        self, prefix: str, limit: int, offset: int
    ) -> Dict:
        """
        Список файлов в S3
        """
        bucket_name = self.config.get("bucket_name")

        response = self.s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix,
            MaxKeys=limit,
        )

        files = []
        for obj in response.get("Contents", []):
            files.append({
                "filename": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"],
                "etag": obj["ETag"],
            })

        return {
            "files": files[offset:offset + limit],
            "total": len(files),
            "has_more": response.get("IsTruncated", False),
        }

    async def _cleanup_s3_files(self, cutoff_date, prefix: str) -> int:
        """
        Очистка старых файлов в S3
        """
        bucket_name = self.config.get("bucket_name")
        deleted_count = 0

        # Получаем список файлов
        response = self.s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix,
        )

        # Удаляем старые файлы
        for obj in response.get("Contents", []):
            if obj["LastModified"].replace(tzinfo=None) < cutoff_date:
                self.s3_client.delete_object(
                    Bucket=bucket_name,
                    Key=obj["Key"],
                )
                deleted_count += 1

        return deleted_count

    async def _check_s3_health(self) -> bool:
        """
        Проверка здоровья S3
        """
        bucket_name = self.config.get("bucket_name")

        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except Exception:
            return False

    # Локальные методы
    async def _upload_to_local(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        metadata: Optional[Dict],
    ) -> str:
        """
        Загрузка файла в локальное хранилище
        """
        local_path = self.config.get("local_path")
        file_path = os.path.join(local_path, "uploads", filename)

        # Сохраняем файл
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_data)

        # Сохраняем метаданные
        if metadata:
            meta_path = file_path + ".meta"
            import json
            async with aiofiles.open(meta_path, "w") as f:
                await f.write(json.dumps(metadata))

        # Генерируем URL (для локального хранилища это путь)
        url = f"/storage/uploads/{filename}"
        return url

    async def _download_from_local(self, filename: str, destination_path: str):
        """
        Скачивание файла из локального хранилища
        """
        local_path = self.config.get("local_path")
        source_path = os.path.join(local_path, "uploads", filename)

        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Файл не найден: {filename}")

        # Копируем файл
        async with aiofiles.open(source_path, "rb") as src:
            async with aiofiles.open(destination_path, "wb") as dst:
                await dst.write(await src.read())

    async def _delete_from_local(self, filename: str) -> bool:
        """
        Удаление файла из локального хранилища
        """
        local_path = self.config.get("local_path")
        file_path = os.path.join(local_path, "uploads", filename)
        meta_path = file_path + ".meta"

        # Удаляем файл
        if os.path.exists(file_path):
            os.remove(file_path)

        # Удаляем метаданные если есть
        if os.path.exists(meta_path):
            os.remove(meta_path)

        return os.path.exists(file_path)

    async def _get_local_url(self, filename: str) -> str:
        """
        Получение URL файла из локального хранилища
        """
        return f"/storage/uploads/{filename}"

    async def _local_file_exists(self, filename: str) -> bool:
        """
        Проверка существования файла в локальном хранилище
        """
        local_path = self.config.get("
