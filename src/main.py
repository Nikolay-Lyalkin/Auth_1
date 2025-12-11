from contextlib import asynccontextmanager
from typing import Any

from async_fastapi_jwt_auth import AuthJWT
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

from src.core.config import settings
from src.db import redis_db
from src.handlers.user_roles import router as user_role_router
from src.handlers.users import router as user_router


@AuthJWT.load_config
def get_config():
    return settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis_db.redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)
    yield
    # Shutdown


# Сначала создаем app
app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/openapi",
    openapi_url="/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


def custom_openapi() -> dict[str, Any]:
    """Кастомная OpenAPI схема с поддержкой JWT аутентификации"""
    if app.openapi_schema:
        return app.openapi_schema

    # Используем get_openapi вместо app.openapi() чтобы избежать рекурсии
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description=f"{settings.PROJECT_NAME} API with JWT authentication",
        routes=app.routes,
    )

    # Добавляем security схему для JWT аутентификации
    openapi_schema.setdefault("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token as: **Bearer &lt;token&gt;**",
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Применяем кастомную OpenAPI схему
app.openapi = custom_openapi

app.include_router(user_router, prefix="", tags=["user"])
app.include_router(user_role_router, prefix="", tags=["user_role"])
