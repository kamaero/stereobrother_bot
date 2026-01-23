"""
Minimal FastAPI application for testing purposes.
This is a simplified version of the main application.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.settings import settings

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting StereoBrother Bot application")
    yield
    # Shutdown
    logger.info("Shutting down StereoBrother Bot application")


# Создание приложения FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered audio processing bot",
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
    """Middleware для логирования HTTP запросов."""
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


# Dependency для аутентификации (упрощенная версия)
async def authenticate_request(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict:
    """Упрощенная аутентификация для тестирования."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима аутентификация",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # В реальном приложении здесь была бы проверка токена
    return {"user_id": "test_user", "role": "user"}


async def get_current_user(user: Dict = Depends(authenticate_request)) -> Dict:
    """Получение текущего пользователя."""
    return user


# Основные маршруты
@app.get("/")
async def root():
    """Корневой маршрут."""
    return {
        "message": "Welcome to StereoBrother Bot API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None,
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": "2024-01-01T00:00:00Z",  # Заглушка
    }


@app.get("/api/user/profile")
async def get_user_profile(user: Dict = Depends(get_current_user)):
    """Получение профиля пользователя."""
    return {
        "id": user["user_id"],
        "role": user["role"],
        "is_active": True,
    }


# Маршруты для обработки аудио (заглушки)
@app.post("/api/audio/upload")
async def upload_audio(user: Dict = Depends(get_current_user)):
    """Загрузка аудио файла."""
    return {
        "task_id": "test_task_123",
        "status": "pending",
        "message": "Audio upload received",
    }


@app.post("/api/audio/enhance")
async def enhance_audio(user: Dict = Depends(get_current_user)):
    """Улучшение качества аудио."""
    return {
        "task_id": "test_task_456",
        "status": "processing",
        "message": "Audio enhancement started",
    }


@app.post("/api/audio/denoise")
async def denoise_audio(user: Dict = Depends(get_current_user)):
    """Удаление шума из аудио."""
    return {
        "task_id": "test_task_789",
        "status": "processing",
        "message": "Audio denoising started",
    }


@app.post("/api/audio/separate")
async def separate_stems(user: Dict = Depends(get_current_user)):
    """Разделение аудио на дорожки."""
    return {
        "task_id": "test_task_abc",
        "status": "processing",
        "message": "Stem separation started",
    }


@app.post("/api/audio/master")
async def master_audio(user: Dict = Depends(get_current_user)):
    """Мастеринг аудио."""
    return {
        "task_id": "test_task_def",
        "status": "processing",
        "message": "Audio mastering started",
    }


@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str, user: Dict = Depends(get_current_user)):
    """Получение статуса задачи."""
    return {
        "task_id": task_id,
        "status": "completed",
        "result_url": f"/api/results/{task_id}",
    }


@app.get("/api/history")
async def get_processing_history(user: Dict = Depends(get_current_user)):
    """Получение истории обработки."""
    return {
        "history": [],
        "total": 0,
    }


# Маршруты для пользователей (заглушки)
@app.post("/api/auth/register")
async def register_user():
    """Регистрация нового пользователя."""
    return {
        "user_id": "new_user_123",
        "message": "User registered successfully",
    }


@app.post("/api/auth/login")
async def login_user():
    """Вход пользователя."""
    return {
        "access_token": "test_token_123",
        "token_type": "bearer",
        "expires_in": 3600,
    }


@app.post("/api/auth/refresh")
async def refresh_token():
    """Обновление токена."""
    return {
        "access_token": "refreshed_token_123",
        "token_type": "bearer",
        "expires_in": 3600,
    }


# Маршруты для подписок (заглушки)
@app.post("/api/subscription/create")
async def create_subscription(user: Dict = Depends(get_current_user)):
    """Создание подписки."""
    return {
        "subscription_id": "sub_123",
        "status": "active",
        "message": "Subscription created successfully",
    }


@app.get("/api/subscription/status")
async def get_subscription_status(user: Dict = Depends(get_current_user)):
    """Получение статуса подписки."""
    return {
        "subscription_id": "sub_123",
        "status": "active",
        "plan": "premium",
        "expires_at": "2024-12-31T23:59:59Z",
    }


# Обработчик ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик HTTP исключений."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик общих исключений."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )


# Точка входа для запуска приложения
if __name__ == "__main__":
    uvicorn.run(
        "src.main_minimal:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )
