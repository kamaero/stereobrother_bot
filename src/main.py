"""
Основной файл приложения FastAPI для бота обработки аудио
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config.settings import settings
from services.audio_processor import AudioProcessor
from services.user_manager import UserManager
from services.payment_service import PaymentService
from utils.validators import validate_audio_file
from models.schemas import (
    AudioUploadRequest,
    AudioProcessRequest,
    AudioEnhancementRequest,
    AudioDenoiseRequest,
    StemSeparationRequest,
    MasteringRequest,
    UserRegistration,
    UserLogin,
    SubscriptionRequest,
    ProcessResponse,
    UserResponse,
    SubscriptionResponse,
)

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Инициализация сервисов
security = HTTPBearer()
audio_processor = AudioProcessor()
user_manager = UserManager()
payment_service = PaymentService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения
    """
    # Инициализация при запуске
    logger.info(f"Запуск приложения {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Среда: {settings.ENVIRONMENT}")
    logger.info(f"Отладка: {settings.DEBUG}")

    # Инициализация сервисов
    await user_manager.initialize()
    await audio_processor.initialize()

    yield

    # Очистка при завершении
    logger.info("Завершение работы приложения")
    await user_manager.shutdown()
    await audio_processor.shutdown()


# Создание экземпляра FastAPI приложения
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Бот для ИИ-обработки и реставрации аудио",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware для логирования входящих запросов
    """
    logger.info(f"Запрос: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        logger.info(f"Ответ: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}")
        raise


# Middleware для проверки аутентификации
@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    """
    Middleware для проверки аутентификации пользователя
    """
    # Исключаем публичные эндпоинты из проверки
    public_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json",
                   "/api/auth/register", "/api/auth/login"]

    if request.url.path in public_paths:
        return await call_next(request)

    # Проверяем токен для защищенных эндпоинтов
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Требуется аутентификация"}
        )

    try:
        # Извлекаем токен из заголовка
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверная схема аутентификации"
            )

        # Проверяем токен
        user = await user_manager.verify_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный или просроченный токен"
            )

        # Добавляем пользователя в состояние запроса
        request.state.user = user

    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Неверный формат заголовка Authorization"}
        )
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )

    return await call_next(request)


# Зависимость для получения текущего пользователя
async def get_current_user(request: Request) -> Dict:
    """
    Зависимость для получения текущего пользователя из запроса
    """
    return request.state.user


# Эндпоинты состояния
@app.get("/")
async def root():
    """
    Корневой эндпоинт
    """
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
async def health_check():
    """
    Эндпоинт проверки здоровья приложения
    """
    health_status = {
        "status": "healthy",
        "services": {
            "database": await user_manager.check_health(),
            "audio_processor": await audio_processor.check_health(),
            "storage": True,  # TODO: Добавить проверку хранилища
        }
    }

    # Проверяем статус всех сервисов
    if not all(health_status["services"].values()):
        health_status["status"] = "unhealthy"

    return health_status


# Эндпоинты аутентификации
@app.post("/api/auth/register", response_model=UserResponse)
async def register_user(user_data: UserRegistration):
    """
    Регистрация нового пользователя
    """
    try:
        user = await user_manager.register_user(
            email=user_data.email,
            password=user_data.password,
            username=user_data.username
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/auth/login", response_model=Dict)
async def login_user(login_data: UserLogin):
    """
    Вход пользователя в систему
    """
    try:
        tokens = await user_manager.login_user(
            email=login_data.email,
            password=login_data.password
        )
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@app.post("/api/auth/refresh", response_model=Dict)
async def refresh_token(refresh_token: str):
    """
    Обновление access токена
    """
    try:
        tokens = await user_manager.refresh_token(refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# Эндпоинты пользователя
@app.get("/api/user/profile", response_model=UserResponse)
async def get_user_profile(user: Dict = Depends(get_current_user)):
    """
    Получение профиля пользователя
    """
    return user


@app.get("/api/user/usage")
async def get_user_usage(user: Dict = Depends(get_current_user)):
    """
    Получение информации об использовании лимитов
    """
    usage = await user_manager.get_user_usage(user["id"])
    return {
        "daily_generations": usage["daily_generations"],
        "daily_limit": settings.DAILY_GENERATION_LIMIT,
        "subscription_active": usage["subscription_active"],
        "subscription_ends_at": usage["subscription_ends_at"],
    }


# Эндпоинты обработки аудио
@app.post("/api/audio/upload", response_model=ProcessResponse)
async def upload_audio(
    request: AudioUploadRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Загрузка аудиофайла для обработки
    """
    try:
        # Проверяем лимиты пользователя
        if not await user_manager.can_process_audio(user["id"]):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Достигнут дневной лимит обработки"
            )

        # Валидируем файл
        validation_result = await validate_audio_file(
            file_path=request.file_path,
            max_duration=settings.max_file_duration_seconds
        )

        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result["error"]
            )

        # Создаем задачу обработки
        task_id = await audio_processor.create_processing_task(
            user_id=user["id"],
            file_path=request.file_path,
            original_filename=request.original_filename
        )

        # Увеличиваем счетчик обработок
        await user_manager.increment_processing_count(user["id"])

        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Файл загружен и поставлен в очередь на обработку"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при загрузке аудио: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при загрузке файла"
        )


@app.post("/api/audio/enhance", response_model=ProcessResponse)
async def enhance_audio(
    request: AudioEnhancementRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Улучшение качества аудио
    """
    try:
        # Проверяем доступность задачи
        task = await audio_processor.get_task(request.task_id)
        if not task or task["user_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена"
            )

        # Запускаем улучшение
        result = await audio_processor.enhance_audio(
            task_id=request.task_id,
            mode=request.mode,
            instrument=request.instrument
        )

        return {
            "task_id": request.task_id,
            "status": "processing",
            "result_url": result.get("result_url"),
            "message": "Запущено улучшение качества аудио"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при улучшении аудио: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при улучшении аудио"
        )


@app.post("/api/audio/denoise", response_model=ProcessResponse)
async def denoise_audio(
    request: AudioDenoiseRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Очистка аудио от шумов
    """
    try:
        # Проверяем доступность задачи
        task = await audio_processor.get_task(request.task_id)
        if not task or task["user_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена"
            )

        # Запускаем очистку
        result = await audio_processor.denoise_audio(
            task_id=request.task_id,
            noise_types=request.noise_types
        )

        return {
            "task_id": request.task_id,
            "status": "processing",
            "result_url": result.get("result_url"),
            "message": "Запущена очистка аудио от шумов"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при очистке аудио: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при очистке аудио"
        )


@app.post("/api/audio/separate", response_model=ProcessResponse)
async def separate_stems(
    request: StemSeparationRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Разделение аудио на дорожки
    """
    try:
        # Проверяем доступность задачи
        task = await audio_processor.get_task(request.task_id)
        if not task or task["user_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена"
            )

        # Запускаем разделение
        result = await audio_processor.separate_stems(
            task_id=request.task_id,
            configuration=request.configuration
        )

        return {
            "task_id": request.task_id,
            "status": "processing",
            "result_url": result.get("result_url"),
            "message": "Запущено разделение аудио на дорожки"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при разделении аудио: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при разделении аудио"
        )


@app.post("/api/audio/master", response_model=ProcessResponse)
async def master_audio(
    request: MasteringRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Мастеринг аудио
    """
    try:
        # Проверяем доступность задачи
        task = await audio_processor.get_task(request.task_id)
        if not task or task["user_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена"
            )

        # Запускаем мастеринг
        result = await audio_processor.master_audio(
            task_id=request.task_id,
            preset=request.preset,
            output_format=request.output_format
        )

        return {
            "task_id": request.task_id,
            "status": "processing",
            "result_url": result.get("result_url"),
            "message": "Запущен мастеринг аудио"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при мастеринге аудио: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при мастеринге аудио"
        )


@app.get("/api/audio/task/{task_id}")
async def get_task_status(task_id: str, user: Dict = Depends(get_current_user)):
    """
    Получение статуса задачи обработки
    """
    try:
        task = await audio_processor.get_task(task_id)
        if not task or task["user_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена"
            )

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении статуса задачи: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении статуса задачи"
        )


@app.get("/api/audio/history")
async def get_processing_history(
    limit: int = 10,
    offset: int = 0,
    user: Dict = Depends(get_current_user)
):
    """
    Получение истории обработок пользователя
    """
    try:
        history = await audio_processor.get_user_history(
            user_id=user["id"],
            limit=limit,
            offset=offset
        )
        return history

    except Exception as e:
        logger.error(f"Ошибка при получении истории: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении истории обработок"
        )


# Эндпоинты подписки
@app.post("/api/subscription/create", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Создание подписки
    """
    try:
        subscription = await payment_service.create_subscription(
            user_id=user["id"],
            plan=subscription_data.plan,
            payment_method=subscription_data.payment_method
        )

        return subscription

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка при создании подписки: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании подписки"
        )


@app.get("/api/subscription/status")
async def get_subscription_status(user: Dict = Dep
