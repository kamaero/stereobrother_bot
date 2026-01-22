"""
Валидаторы для аудио файлов и данных
"""

import logging
import os
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Union

import librosa
import soundfile as sf

from config.settings import settings

logger = logging.getLogger(__name__)


async def validate_audio_file(
    file_path: str,
    max_duration: Optional[float] = None,
    min_duration: Optional[float] = None,
    allowed_formats: Optional[List[str]] = None,
    max_file_size: Optional[int] = None,
) -> Dict[str, Union[bool, str]]:
    """
    Валидация аудио файла

    Args:
        file_path: Путь к аудио файлу
        max_duration: Максимальная длительность в секундах
        min_duration: Минимальная длительность в секундах
        allowed_formats: Разрешенные форматы файлов
        max_file_size: Максимальный размер файла в байтах

    Returns:
        Словарь с результатами валидации
    """
    result = {
        "valid": False,
        "error": None,
        "duration": 0.0,
        "sample_rate": 0,
        "channels": 0,
        "format": None,
    }

    try:
        # Проверяем существование файла
        if not os.path.exists(file_path):
            result["error"] = "Файл не существует"
            return result

        # Проверяем размер файла
        file_size = os.path.getsize(file_path)
        if max_file_size and file_size > max_file_size:
            result["error"] = f"Размер файла превышает максимальный ({max_file_size} байт)"
            return result

        # Проверяем MIME тип
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type or not mime_type.startswith("audio/"):
            # Пытаемся определить по расширению
            ext = Path(file_path).suffix.lower()[1:]
            if ext not in settings.SUPPORTED_INPUT_FORMATS:
                result["error"] = f"Неподдерживаемый формат файла: {ext}"
                return result

        # Проверяем разрешенные форматы
        if allowed_formats:
            ext = Path(file_path).suffix.lower()[1:]
            if ext not in allowed_formats:
                result["error"] = f"Формат файла {ext} не разрешен"
                return result

        # Получаем информацию об аудио файле
        try:
            audio_info = sf.info(file_path)
            result["duration"] = audio_info.duration
            result["sample_rate"] = audio_info.samplerate
            result["channels"] = audio_info.channels
            result["format"] = audio_info.format
        except Exception as e:
            result["error"] = f"Не удалось прочитать аудио файл: {str(e)}"
            return result

        # Проверяем длительность
        if max_duration and result["duration"] > max_duration:
            result["error"] = f"Длительность файла ({result['duration']:.1f} сек) превышает максимальную ({max_duration} сек)"
            return result

        if min_duration and result["duration"] < min_duration:
            result["error"] = f"Длительность файла ({result['duration']:.1f} сек) меньше минимальной ({min_duration} сек)"
            return result

        # Проверяем частоту дискретизации
        if result["sample_rate"] < 8000:
            result["error"] = f"Частота дискретизации ({result['sample_rate']} Hz) слишком низкая"
            return result

        if result["sample_rate"] > 192000:
            result["error"] = f"Частота дискретизации ({result['sample_rate']} Hz) слишком высокая"
            return result

        # Проверяем количество каналов
        if result["channels"] > 8:
            result["error"] = f"Слишком много каналов ({result['channels']})"
            return result

        # Проверяем, что файл не пустой
        if result["duration"] <= 0:
            result["error"] = "Файл имеет нулевую длительность"
            return result

        # Все проверки пройдены
        result["valid"] = True
        logger.debug(f"Файл валидирован: {file_path}, длительность: {result['duration']} сек")

    except Exception as e:
        result["error"] = f"Ошибка при валидации файла: {str(e)}"
        logger.error(f"Ошибка при валидации файла {file_path}: {str(e)}")

    return result


def validate_email(email: str) -> Dict[str, Union[bool, str]]:
    """
    Валидация email адреса

    Args:
        email: Email адрес

    Returns:
        Словарь с результатами валидации
    """
    result = {"valid": False, "error": None}

    try:
        # Проверяем наличие @
        if "@" not in email:
            result["error"] = "Email должен содержать символ @"
            return result

        # Разделяем на локальную часть и домен
        local_part, domain = email.split("@", 1)

        # Проверяем локальную часть
        if not local_part or len(local_part) > 64:
            result["error"] = "Локальная часть email должна быть от 1 до 64 символов"
            return result

        # Проверяем домен
        if not domain or "." not in domain:
            result["error"] = "Некорректный домен email"
            return result

        # Проверяем общую длину
        if len(email) > 254:
            result["error"] = "Email слишком длинный (максимум 254 символа)"
            return result

        # Проверяем разрешенные символы
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            result["error"] = "Некорректный формат email"
            return result

        result["valid"] = True

    except Exception as e:
        result["error"] = f"Ошибка при валидации email: {str(e)}"

    return result


def validate_password(password: str) -> Dict[str, Union[bool, str]]:
    """
    Валидация пароля

    Args:
        password: Пароль

    Returns:
        Словарь с результатами валидации
    """
    result = {"valid": False, "error": None, "strength": "weak"}

    try:
        # Проверяем длину
        if len(password) < 8:
            result["error"] = "Пароль должен содержать минимум 8 символов"
            return result

        if len(password) > 128:
            result["error"] = "Пароль слишком длинный (максимум 128 символов)"
            return result

        # Проверяем наличие заглавных букв
        if not any(c.isupper() for c in password):
            result["error"] = "Пароль должен содержать хотя бы одну заглавную букву"
            return result

        # Проверяем наличие строчных букв
        if not any(c.islower() for c in password):
            result["error"] = "Пароль должен содержать хотя бы одну строчную букву"
            return result

        # Проверяем наличие цифр
        if not any(c.isdigit() for c in password):
            result["error"] = "Пароль должен содержать хотя бы одну цифру"
            return result

        # Проверяем наличие специальных символов
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            result["error"] = f"Пароль должен содержать хотя бы один специальный символ ({special_chars})"
            return result

        # Оцениваем сложность пароля
        strength_score = 0

        # Длина
        if len(password) >= 12:
            strength_score += 2
        elif len(password) >= 8:
            strength_score += 1

        # Разнообразие символов
        char_categories = 0
        if any(c.isupper() for c in password):
            char_categories += 1
        if any(c.islower() for c in password):
            char_categories += 1
        if any(c.isdigit() for c in password):
            char_categories += 1
        if any(c in special_chars for c in password):
            char_categories += 1

        if char_categories >= 4:
            strength_score += 2
        elif char_categories >= 3:
            strength_score += 1

        # Определяем уровень сложности
        if strength_score >= 3:
            result["strength"] = "strong"
        elif strength_score >= 2:
            result["strength"] = "medium"
        else:
            result["strength"] = "weak"

        result["valid"] = True

    except Exception as e:
        result["error"] = f"Ошибка при валидации пароля: {str(e)}"

    return result


def validate_username(username: str) -> Dict[str, Union[bool, str]]:
    """
    Валидация имени пользователя

    Args:
        username: Имя пользователя

    Returns:
        Словарь с результатами валидации
    """
    result = {"valid": False, "error": None}

    try:
        # Проверяем длину
        if len(username) < 3:
            result["error"] = "Имя пользователя должно содержать минимум 3 символа"
            return result

        if len(username) > 50:
            result["error"] = "Имя пользователя слишком длинное (максимум 50 символов)"
            return result

        # Проверяем разрешенные символы
        import re
        username_pattern = r'^[a-zA-Z0-9_.-]+$'
        if not re.match(username_pattern, username):
            result["error"] = "Имя пользователя может содержать только буквы, цифры, точки, дефисы и подчеркивания"
            return result

        # Проверяем, что имя не начинается и не заканчивается точкой или дефисом
        if username.startswith(".") or username.startswith("-") or username.startswith("_"):
            result["error"] = "Имя пользователя не может начинаться с точки, дефиса или подчеркивания"
            return result

        if username.endswith(".") or username.endswith("-") or username.endswith("_"):
            result["error"] = "Имя пользователя не может заканчиваться точкой, дефисом или подчеркивания"
            return result

        # Проверяем, что нет двух точек подряд
        if ".." in username:
            result["error"] = "Имя пользователя не может содержать две точки подряд"
            return result

        result["valid"] = True

    except Exception as e:
        result["error"] = f"Ошибка при валидации имени пользователя: {str(e)}"

    return result


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> Dict[str, Union[bool, str]]:
    """
    Валидация расширения файла

    Args:
        filename: Имя файла
        allowed_extensions: Разрешенные расширения

    Returns:
        Словарь с результатами валидации
    """
    result = {"valid": False, "error": None}

    try:
        # Извлекаем расширение
        ext = Path(filename).suffix.lower()
        if not ext:
            result["error"] = "Файл не имеет расширения"
            return result

        # Убираем точку
        ext = ext[1:]

        # Проверяем разрешенные расширения
        if ext not in allowed_extensions:
            result["error"] = f"Расширение .{ext} не разрешено. Разрешенные расширения: {', '.join(allowed_extensions)}"
            return result

        result["valid"] = True

    except Exception as e:
        result["error"] = f"Ошибка при валидации расширения файла: {str(e)}"

    return result


def validate_processing_parameters(parameters: Dict) -> Dict[str, Union[bool, str]]:
    """
    Валидация параметров обработки аудио

    Args:
        parameters: Параметры обработки

    Returns:
        Словарь с результатами валидации
    """
    result = {"valid": False, "error": None}

    try:
        # Проверяем обязательные параметры
        required_params = ["task_id", "processing_type"]
        for param in required_params:
            if param not in parameters:
                result["error"] = f"Отсутствует обязательный параметр: {param}"
                return result

        # Валидируем в зависимости от типа обработки
        processing_type = parameters.get("processing_type")

        if processing_type == "enhancement":
            # Валидация параметров улучшения
            if "mode" not in parameters:
                result["error"] = "Для улучшения требуется параметр 'mode'"
                return result

            valid_modes = ["full_mix", "drums", "guitars", "bass", "strings", "piano", "vocals"]
            if parameters["mode"] not in valid_modes:
                result["error"] = f"Некорректный режим улучшения. Допустимые значения: {', '.join(valid_modes)}"
                return result

        elif processing_type == "denoise":
            # Валидация параметров денойзинга
            if "noise_types" not in parameters:
                result["error"] = "Для денойзинга требуется параметр 'noise_types'"
                return result

            if not isinstance(parameters["noise_types"], list):
                result["error"] = "Параметр 'noise_types' должен быть списком"
                return result

            valid_noise_types = ["crackle", "hiss", "background", "equipment"]
            for noise_type in parameters["noise_types"]:
                if noise_type not in valid_noise_types:
                    result["error"] = f"Некорректный тип шума: {noise_type}. Допустимые значения: {', '.join(valid_noise_types)}"
                    return result

            if "intensity" in parameters:
                intensity = parameters["intensity"]
                if not isinstance(intensity, (int, float)) or intensity < 0 or intensity > 1:
                    result["error"] = "Параметр 'intensity' должен быть числом от 0 до 1"
                    return result

        elif processing_type == "stem_separation":
            # Валидация параметров разделения дорожек
            if "configuration" not in parameters:
                result["error"] = "Для разделения дорожек требуется параметр 'configuration'"
                return result

            valid_configs = ["basic", "advanced"]
            if parameters["configuration"] not in valid_configs:
                result["error"] = f"Некорректная конфигурация. Допустимые значения: {', '.join(valid_configs)}"
                return result

        elif processing_type == "mastering":
            # Валидация параметров мастеринга
            if "preset" not in parameters:
                result["error"] = "Для мастеринга требуется параметр 'preset'"
                return result

            valid_presets = ["podcast", "song", "advertisement"]
            if parameters["preset"] not in valid_presets:
                result["error"] = f"Некорректный пресет. Допустимые значения: {', '.join(valid_presets)}"
                return result

            if "output_format" in parameters:
                valid_formats = ["wav", "mp3"]
                if parameters["output_format"] not in valid_formats:
                    result["error"] = f"Некорректный формат вывода. Допустимые значения: {', '.join(valid_formats)}"
                    return result

        else:
            result["error"] = f"Некорректный тип обработки: {processing_type}"
            return result

        result["valid"] = True

    except Exception as e:
        result["error"] = f"Ошибка при валидации параметров обработки: {str(e)}"

    return result


def validate_subscription_data(data: Dict) -> Dict[str, Union[bool, str]]:
    """
    Валидация данных подписки

    Args:
        data: Данные подписки

    Returns:
        Словарь с результатами валидации
    """
    result = {"valid": False, "error": None}

    try:
        # Проверяем обязательные параметры
        required_params = ["plan", "payment_method"]
        for param in required_params:
            if param not in data:
                result["error"] = f"Отсутствует обязательный параметр: {param}"
                return result

        # Валидируем план
        valid_plans = ["monthly", "yearly"]
        if data["plan"] not in valid_plans:
            result["error"] = f"Некорректный план. Допустимые значения: {', '.join(valid_plans)}"
            return result

        # Валидируем метод оплаты
        valid_payment_methods = ["card", "yoomoney", "sbp"]
        if data["payment_method"] not in valid_payment_methods:
            result["error"] = f"Некор
