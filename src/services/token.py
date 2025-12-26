from datetime import datetime

import jwt
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.db.postgres import get_session
from src.models.user import User


class TokenService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_current_user_required(self, authorize: AuthJWT, user_id: str) -> dict:
        """Получить пользователя (обязательная авторизация)"""

        try:
            await authorize.jwt_required()
            user_id_from_jwt = await authorize.get_jwt_subject()

            if user_id_from_jwt == user_id:
                return {"user_id": user_id_from_jwt, "authenticated": True}
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет прав на доступ к данным этого пользователя"
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def generate_access_token(self, user_id: str, authorize: AuthJWT):
        """Генерация токена с дополнительными claims"""

        stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one()

        # Дополнительные данные в токене
        additional_claims = {"user_id": user_id, "is_active": True, "token_type": "access", "role": user.role.name}

        access_token = await authorize.create_access_token(
            subject=user_id, user_claims=additional_claims, expires_time=86400 * 7  # 7 дней
        )

        return access_token

    async def generate_refresh_token(self, user_id: str, authorize: AuthJWT):
        """Генерация refresh токена"""

        stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one()

        additional_claims = {"user_id": user_id, "token_type": "refresh", "role": user.role.name}

        refresh_token = await authorize.create_refresh_token(
            subject=user_id, user_claims=additional_claims, expires_time=86400 * 30  # 30 дней
        )

        return refresh_token

    async def refresh_access_token(self, authorize: AuthJWT):
        """Обновление access токена с помощью refresh токена"""
        try:
            # Проверяем, что передан валидный refresh токен
            await authorize.jwt_refresh_token_required()

            # Получаем идентификатор пользователя из токена
            current_user = await authorize.get_jwt_subject()

            # Получаем claims для проверки типа токена
            claims = await authorize.get_raw_jwt()

            # Проверяем, что это действительно refresh токен
            if claims.get("token_type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")

            # Генерируем новый access токен
            new_access_token = await self.generate_access_token(current_user, authorize)

            return new_access_token

        except AuthJWTException as e:
            raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")

    async def add_token_in_blacklist(self, authorize: AuthJWT, redis: Redis):
        """Добавляет токен в блэклист"""

        jwt_data = await authorize.get_raw_jwt()
        jti = jwt_data.get("jti")  # JWT ID - уникальный идентификатор токена
        exp_timestamp = jwt_data.get("exp")  # Время истечения (timestamp)
        user_id = jwt_data.get("sub")  # id пользователя
        current_time = int(datetime.now().timestamp())
        ttl_seconds = exp_timestamp - current_time
        blacklist_key = jti
        await redis.setex(
            blacklist_key,  # ключ
            ttl_seconds,  # время хранения
            user_id,  # значение
        )

    async def get_token_from_redis(self, authorize: AuthJWT, redis: Redis):
        """Проверяет есть ли токен в блэклисте"""

        jwt_data = await authorize.get_raw_jwt()
        if await redis.get(jwt_data.get("jti")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пожалуйста пройдите авторизацию")
        return True

    def decode_token(token: str) -> dict | None:
        """Функция декодирует токен"""
        try:
            return jwt.decode(token, settings.authjwt_secret_key, algorithms=[settings.authjwt_algorithm])
        except Exception:
            return None


def get_token_service(db: AsyncSession = Depends(get_session)) -> TokenService:
    result = TokenService(db)
    return result


class JWTBearer(HTTPBearer):
    """
    Класс - наследник fastapi.security.HTTPBearer. Рекомендуем исследовать этот класс.
    Метод `__call__` класса HTTPBearer возвращает объект HTTPAuthorizationCredentials из заголовка `Authorization`

    class HTTPAuthorizationCredentials(BaseModel):
        scheme: str #  'Bearer'
        credentials: str #  сам токен в кодировке Base64

    FastAPI при использовании класса HTTPBearer добавит всё необходимое для авторизации в Swagger документацию.
    """

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict:
        """
        Переопределение метода родительского класса HTTPBearer.
        Логика проста: достаём токен из заголовка и декодируем его.
        В результате возвращаем словарь из payload токена или выбрасываем исключение.
        Так как далее объект этого класса будет использоваться как зависимость Depends(...),
        то при этом будет вызван метод `__call__`.
        """
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authorization code.")
        if not credentials.scheme == "Bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Only Bearer token might be accepted")
        decoded_token = self.parse_token(credentials.credentials)
        if not decoded_token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired token.")
        return decoded_token

    @staticmethod
    def parse_token(jwt_token: str) -> dict | None:
        return TokenService.decode_token(jwt_token)


security_jwt = JWTBearer()
