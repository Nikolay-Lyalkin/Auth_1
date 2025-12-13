from uuid import UUID

import dotenv
import user_agents
from async_fastapi_jwt_auth import AuthJWT
from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.postgres import get_session
from src.models.user import LoginHistory
from src.schemas.login_history import LoginHistoryCreateSchema, LoginHistoryResponseSchema
from src.services.token import TokenService

dotenv.load_dotenv()


class LoginHistoryService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_login_history_from_request(
        self,
        request: Request,
        user_id: UUID,
        login_status: str = "success",
    ) -> LoginHistoryResponseSchema:
        """Создание записи истории логина из данных запроса"""

        # Извлекаем IP-адрес клиента
        ip_address = await self.get_client_ip(request)

        # Извлекаем User-Agent
        user_agent_header = request.headers.get("user-agent", "")

        # Определяем тип устройства из User-Agent
        device_type = await self.parse_device_type(user_agent_header)

        # Создаем схему с извлеченными данными
        history_data = LoginHistoryCreateSchema(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent_header,
            device_type=device_type,
            login_status=login_status,
        )

        # Создаем и сохраняем запись в БД
        history_db = LoginHistory(**history_data.model_dump())
        self.db.add(history_db)
        await self.db.commit()
        await self.db.refresh(history_db)

        return LoginHistoryResponseSchema.model_validate(history_db)

    async def get_client_ip(self, request: Request) -> str:
        """
        Извлекает реальный IP-адрес клиента с учетом прокси
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
            return client_ip

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def parse_device_type(self, user_agent: str) -> str:
        """
        Определяет тип устройства из User-Agent строки
        """
        if not user_agent:
            return "unknown"

        try:
            ua = user_agents.parse(user_agent)

            if ua.is_mobile:
                return "mobile"
            elif ua.is_tablet:
                return "tablet"
            elif ua.is_pc:
                return "desktop"
            elif ua.is_bot:
                return "bot"
            else:
                return "other"
        except:
            return "unknown"

    async def get_login_history(self, user_id: str, token_service: TokenService, authorize: AuthJWT, redis: Redis):
        """Получение истории входа пользователя"""
        await token_service.get_token_from_redis(authorize, redis)

        query = select(LoginHistory).where(LoginHistory.user_id == user_id)
        result = await self.db.execute(query)
        history = result.scalars().all()

        if history:
            return list(history)


def get_login_history(db: AsyncSession = Depends(get_session)) -> LoginHistoryService:
    result = LoginHistoryService(db)
    return result
