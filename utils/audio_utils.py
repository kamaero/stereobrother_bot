"""
Утилиты для работы с аудио файлами
"""

import asyncio
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from scipy import signal

from config.settings import settings

logger = logging.getLogger(__name__)


async def load_audio_file(
    file_path: str,
    sample_rate: Optional[int] = None,
    mono: bool = False,
    duration: Optional[float] = None,
) -> Tuple[np.ndarray, int]:
    """
    Асинхронная загрузка аудио файла

    Args:
        file_path: Путь к аудио файлу
        sample_rate: Целевая частота дискретизации (None - оригинальная)
        mono: Конвертировать в моно
        duration: Максимальная длительность в секундах

    Returns:
        Кортеж (аудио данные, частота дискретизации)

    Raises:
        ValueError: Если файл не существует или не может быть загружен
    """
    if not os.path.exists(file_path):
        raise ValueError(f"Файл не существует: {file_path}")

    try:
        # Используем librosa для загрузки аудио
        audio_data, sr = librosa.load(
            file_path,
            sr=sample_rate,
            mono=mono,
            duration=duration,
            res_type="kaiser_fast",
        )

        # Если требуется моно, но файл стерео
        if mono and audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=0)

        logger.debug(
            f"Загружен аудио файл: {file_path}, SR: {sr}, форма: {audio_data.shape}"
        )
        return audio_data, sr

    except Exception as e:
        logger.error(f"Ошибка при загрузке аудио файла {file_path}: {str(e)}")
        raise ValueError(f"Не удалось загрузить аудио файл: {str(e)}")


async def save_audio_file(
    file_path: str,
    audio_data: np.ndarray,
    sample_rate: int,
    format: str = "wav",
    subtype: str = "PCM_16",
) -> str:
    """
    Асинхронное сохранение аудио файла

    Args:
        file_path: Путь для сохранения
        audio_data: Аудио данные
        sample_rate: Частота дискретизации
        format: Формат файла (wav, flac, etc.)
        subtype: Подтип (PCM_16, PCM_24, FLOAT, etc.)

    Returns:
        Путь к сохраненному файлу
    """
    try:
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Сохраняем файл
        sf.write(file_path, audio_data, sample_rate, format=format, subtype=subtype)

        logger.debug(
            f"Сохранен аудио файл: {file_path}, SR: {sample_rate}, форма: {audio_data.shape}"
        )
        return file_path

    except Exception as e:
        logger.error(f"Ошибка при сохранении аудио файла {file_path}: {str(e)}")
        raise ValueError(f"Не удалось сохранить аудио файл: {str(e)}")


async def get_audio_info(file_path: str) -> Dict:
    """
    Получение информации об аудио файле

    Args:
        file_path: Путь к аудио файлу

    Returns:
        Словарь с информацией об аудио файле
    """
    try:
        # Используем soundfile для получения информации
        info = sf.info(file_path)

        # Получаем размер файла
        file_size = os.path.getsize(file_path)

        # Получаем битрейт
        bitrate = (file_size * 8) / info.duration if info.duration > 0 else 0

        # Получаем информацию о каналах
        channels = info.channels
        channel_mode = (
            "mono"
            if channels == 1
            else "stereo"
            if channels == 2
            else f"{channels} channels"
        )

        audio_info = {
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "format": info.format,
            "subtype": info.subtype,
            "duration": info.duration,
            "sample_rate": info.samplerate,
            "channels": channels,
            "channel_mode": channel_mode,
            "frames": info.frames,
            "file_size": file_size,
            "bitrate": bitrate,
            "bit_depth": _get_bit_depth(info.subtype),
        }

        logger.debug(f"Получена информация об аудио файле: {file_path}")
        return audio_info

    except Exception as e:
        logger.error(
            f"Ошибка при получении информации об аудио файле {file_path}: {str(e)}"
        )
        raise ValueError(f"Не удалось получить информацию об аудио файле: {str(e)}")


async def convert_audio_format(
    input_path: str,
    output_path: str,
    output_format: str = "wav",
    sample_rate: Optional[int] = None,
    channels: Optional[int] = None,
    bit_depth: Optional[int] = None,
) -> str:
    """
    Конвертация аудио файла в другой формат

    Args:
        input_path: Путь к исходному файлу
        output_path: Путь для сохранения результата
        output_format: Целевой формат (wav, mp3, flac, etc.)
        sample_rate: Целевая частота дискретизации
        channels: Целевое количество каналов
        bit_depth: Целевая глубина бит

    Returns:
        Путь к конвертированному файлу
    """
    try:
        # Загружаем аудио
        audio_data, original_sr = await load_audio_file(input_path)

        # Применяем ресемплинг если нужно
        if sample_rate and sample_rate != original_sr:
            audio_data = await resample_audio(audio_data, original_sr, sample_rate)
            sr = sample_rate
        else:
            sr = original_sr

        # Изменяем количество каналов если нужно
        if channels:
            audio_data = await change_channels(audio_data, channels)

        # Определяем subtype для сохранения
        subtype = _get_subtype_for_bit_depth(bit_depth) if bit_depth else "PCM_16"

        # Сохраняем в нужном формате
        await save_audio_file(
            output_path, audio_data, sr, format=output_format, subtype=subtype
        )

        logger.info(f"Конвертирован аудио файл: {input_path} -> {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Ошибка при конвертации аудио файла {input_path}: {str(e)}")
        raise ValueError(f"Не удалось конвертировать аудио файл: {str(e)}")


async def normalize_audio(
    audio_data: np.ndarray,
    target_level: float = -1.0,
    method: str = "peak",
) -> np.ndarray:
    """
    Нормализация аудио

    Args:
        audio_data: Аудио данные
        target_level: Целевой уровень в dBFS (-1.0 = -1 dBFS)
        method: Метод нормализации (peak, rms, loudness)

    Returns:
        Нормализованные аудио данные
    """
    if audio_data.size == 0:
        return audio_data

    try:
        if method == "peak":
            # Пиковая нормализация
            peak = np.max(np.abs(audio_data))
            if peak > 0:
                target_linear = 10 ** (target_level / 20)
                gain = target_linear / peak
                normalized = audio_data * gain
            else:
                normalized = audio_data

        elif method == "rms":
            # RMS нормализация
            rms = np.sqrt(np.mean(audio_data**2))
            if rms > 0:
                target_rms = 10 ** (target_level / 20)
                gain = target_rms / rms
                normalized = audio_data * gain
            else:
                normalized = audio_data

        elif method == "loudness":
            # Нормализация по громкости (LUFS)
            loudness = await calculate_loudness(audio_data)
            gain = target_level - loudness
            normalized = audio_data * (10 ** (gain / 20))

        else:
            logger.warning(
                f"Неизвестный метод нормализации: {method}, используется peak"
            )
            normalized = await normalize_audio(audio_data, target_level, "peak")

        # Ограничиваем чтобы избежать клиппинга
        normalized = np.clip(normalized, -1.0, 1.0)

        logger.debug(
            f"Нормализовано аудио, метод: {method}, целевой уровень: {target_level} dBFS"
        )
        return normalized

    except Exception as e:
        logger.error(f"Ошибка при нормализации аудио: {str(e)}")
        return audio_data


async def calculate_loudness(audio_data: np.ndarray, sample_rate: int = 44100) -> float:
    """
    Расчет громкости в LUFS (ITU-R BS.1770-4)

    Args:
        audio_data: Аудио данные
        sample_rate: Частота дискретизации

    Returns:
        Громкость в LUFS
    """
    try:
        # Простая реализация расчета громкости
        # Для полноценной реализации нужна библиотека pyloudnorm

        # Преобразуем в моно если нужно
        if audio_data.ndim > 1:
            audio_mono = np.mean(audio_data, axis=0)
        else:
            audio_mono = audio_data

        # К-фильтр (приблизительно)
        # В реальной реализации нужно использовать правильные коэффициенты
        b = [1.0, -1.69065929318241, 0.73248077421585]
        a = [1.0, -1.99004745483398, 0.99007225036621]
        k_filtered = signal.lfilter(b, a, audio_mono)

        # Расчет RMS
        rms = np.sqrt(np.mean(k_filtered**2))

        # Преобразование в LUFS
        if rms > 0:
            loudness = 20 * np.log10(rms) - 0.691  # Эмпирическая поправка
        else:
            loudness = -70  # Минимальное значение

        return float(loudness)

    except Exception as e:
        logger.error(f"Ошибка при расчете громкости: {str(e)}")
        return -20.0  # Значение по умолчанию


async def resample_audio(
    audio_data: np.ndarray,
    original_sr: int,
    target_sr: int,
    method: str = "kaiser_fast",
) -> np.ndarray:
    """
    Ресемплинг аудио

    Args:
        audio_data: Аудио данные
        original_sr: Исходная частота дискретизации
        target_sr: Целевая частота дискретизация
        method: Метод ресемплинга

    Returns:
        Ресемплированные аудио данные
    """
    if original_sr == target_sr:
        return audio_data

    try:
        # Используем librosa для ресемплинга
        resampled = librosa.resample(
            audio_data,
            orig_sr=original_sr,
            target_sr=target_sr,
            res_type=method,
        )

        logger.debug(f"Ресемплировано аудио: {original_sr} Hz -> {target_sr} Hz")
        return resampled

    except Exception as e:
        logger.error(f"Ошибка при ресемплинге аудио: {str(e)}")
        raise ValueError(f"Не удалось ресемплировать аудио: {str(e)}")


async def change_channels(
    audio_data: np.ndarray,
    target_channels: int,
) -> np.ndarray:
    """
    Изменение количества каналов аудио

    Args:
        audio_data: Аудио данные
        target_channels: Целевое количество каналов

    Returns:
        Аудио данные с измененным количеством каналов
    """
    current_channels = 1 if audio_data.ndim == 1 else audio_data.shape[0]

    if current_channels == target_channels:
        return audio_data

    try:
        if target_channels == 1:
            # Конвертация в моно
            if current_channels > 1:
                converted = np.mean(audio_data, axis=0)
            else:
                converted = audio_data

        elif target_channels == 2:
            # Конвертация в стерео
            if current_channels == 1:
                # Дуплицируем моно канал
                converted = np.stack([audio_data, audio_data], axis=0)
            elif current_channels > 2:
                # Берем первые два канала
                converted = audio_data[:2, :]
            else:
                converted = audio_data

        else:
            # Для большего количества каналов
            if current_channels < target_channels:
                # Дублируем существующие каналы
                converted = np.zeros((target_channels, audio_data.shape[-1]))
                for i in range(target_channels):
                    converted[i] = audio_data[i % current_channels]
            else:
                # Берем нужное количество каналов
                converted = audio_data[:target_channels, :]

        logger.debug(f"Изменены каналы аудио: {current_channels} -> {target_channels}")
        return converted

    except Exception as e:
        logger.error(f"Ошибка при изменении каналов аудио: {str(e)}")
        raise ValueError(f"Не удалось изменить количество каналов: {str(e)}")


async def trim_silence(
    audio_data: np.ndarray,
    sample_rate: int,
    top_db: float = 30.0,
    frame_length: int = 2048,
    hop_length: int = 512,
) -> np.ndarray:
    """
    Обрезка тишины в начале и конце аудио

    Args:
        audio_data: Аудио данные
        sample_rate: Частота дискретизации
        top_db: Порог в dB для определения тишины
        frame_length: Длина фрейма для анализа
        hop_length: Шаг для анализа

    Returns:
        Аудио данные с обрезанной тишиной
    """
    try:
        # Используем librosa для обрезки тишины
        trimmed, _ = librosa.effects.trim(
            audio_data,
            top_db=top_db,
            frame_length=frame_length,
            hop_length=hop_length,
        )

        logger.debug(f"Обрезана тишина в аудио, порог: {top_db} dB")
        return trimmed

    except Exception as e:
        logger.error(f"Ошибка при обрезке тишины: {str(e)}")
        return audio_data


async def apply_fade(
    audio_data: np.ndarray,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
) -> np.ndarray:
    """
    Применение фейдов к аудио

    Args:
        audio_data: Аудио данные
        fade_in: Длительность фейд-ина в секундах
        fade_out: Длительность фейд-аута в секундах

    Returns:
        Аудио данные с фейдами
    """
    try:
        if fade_in <= 0 and fade_out <= 0:
            return audio_data

        result = audio_data.copy()

        # Применяем фейд-ин
        if fade_in > 0:
            fade_in_samples = int(fade_in * len(audio_data))
            if fade_in_samples > 0:
                fade_in_curve = np.linspace(0, 1, fade_in_samples)
                if audio_data.ndim > 1:
                    # Для многоканального аудио
                    for channel in range(audio_data.shape[0]):
                        result[channel, :fade_in_samples] *= fade_in_curve
                else:
                    # Для моно аудио
                    result[:fade_in_samples] *= fade_in_curve

        # Применяем фейд-аут
        if fade_out > 0:
            fade_out_samples = int(fade_out * len(audio_data))
            if fade_out_samples > 0:
                fade_out_curve = np.linspace(1, 0, fade_out_samples)
                if audio_data.ndim > 1:
                    # Для многоканального аудио
                    for channel in range(audio_data.shape[0]):
                        result[channel, -fade_out_samples:] *= fade_out_curve
                else:
                    # Для моно аудио
                    result[-fade_out_samples:] *= fade_out_curve

        logger.debug(f"Применены фейды: in={fade_in}s, out={fade_out}s")
        return result

    except Exception as e:
        logger.error(f"Ошибка при применении фейдов: {str(e)}")
        return audio_data


async def validate_audio_file(
    file_path: str,
    max_duration: Optional[float] = None,
    min_duration: Optional[float] = None,
    allowed_formats: Optional[list] = None,
) -> Dict[str, Union[bool, str]]:
    """
    Валидация аудио файла

    Args:
        file_path: Путь к аудио файлу
        max_duration: Максимальная длительность в секундах
        min_duration: Минимальная длительность в секундах
        allowed_formats: Разрешенные форматы файлов

    Returns:
        Словарь с результатами валидации
    """
