from datetime import datetime

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import HTTPException, status
from redis.asyncio import Redis


class TokenService:

    async def get_current_user_required(self, authorize: AuthJWT) -> dict:
        """Получить пользователя (обязательная авторизация)"""

        try:
            await authorize.jwt_required()
            user_id = await authorize.get_jwt_subject()
            return {"user_id": user_id, "authenticated": True}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def generate_access_token(self, user_id: str, authorize: AuthJWT):
        """Генерация токена с дополнительными claims"""

        # Дополнительные данные в токене
        additional_claims = {"user_id": user_id, "is_active": True, "token_type": "access"}

        access_token = await authorize.create_access_token(
            subject=user_id, user_claims=additional_claims, expires_time=86400 * 7  # 7 дней
        )

        return access_token

    async def generate_refresh_token(self, user_id: str, authorize: AuthJWT):
        """Генерация refresh токена"""
        additional_claims = {"user_id": user_id, "token_type": "refresh"}

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
        if await redis.exists(jwt_data.get("jti")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted. Please login again."
            )
        return True


def get_token_service() -> TokenService:
    return TokenService()
