from datetime import datetime

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import HTTPException, status, Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на доступ к данным этого пользователя"
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Пожалуйста пройдите авторизацию"
            )
        return True


def get_token_service(db: AsyncSession = Depends(get_session)) -> TokenService:
    result = TokenService(db)
    return result
