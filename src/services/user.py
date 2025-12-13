import dotenv
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import UserNotFound, UserInDB
from src.db.postgres import get_session
from src.models.user import Role, User
from src.schemas.users import UserAuthSchema, UserCreateSchema, UserUpdateSchema
from src.services.login_history import LoginHistoryService
from src.services.token import TokenService

dotenv.load_dotenv()


class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreateSchema, role_name: str = "user") -> User:
        """Создание пользователя с ролью по умолчанию"""

        query = await self.db.execute(select(Role).filter(Role.name == role_name))
        user_role = query.scalar_one_or_none()

        user = User(
            login=user_data.login,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role_id=user_role.id,
        )
        query = await self.db.execute(select(User).filter(User.login == user.login))
        user_in_db = query.scalar_one_or_none()

        if user_in_db:
            raise UserInDB("Пользователь с таким логином уже существует")
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def auth_user(
        self,
        user_auth: UserAuthSchema,
        request: Request,
        login_history_service: LoginHistoryService,
    ):
        """Авторизация пользователя"""
        user_auth_dto = jsonable_encoder(user_auth)
        query = select(User).where(User.login == str(user_auth_dto["login"]))
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if user:
            check_hash_password = user.check_password(user_auth_dto["password"])
            if check_hash_password:
                await login_history_service.create_login_history_from_request(request, user.id)
                return user
        elif not user:
            raise UserNotFound

    async def update_user(
        self,
        user_id: str,
        update_data: UserUpdateSchema,
        current_user: dict,
        authorize: AuthJWT,
        redis: Redis,
        token_service: TokenService,
    ) -> User:
        """Обновление данных пользователя"""

        await token_service.get_token_from_redis(authorize, redis)
        user = await self.db.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()
        if not user:
            raise UserNotFound("User not found")

        if current_user.get("user_id") == str(user.id):

            update_dict = update_data.model_dump(exclude_unset=True)

            if "new_password" in update_dict:
                user.set_password(update_dict["new_password"])
                del update_dict["new_password"]

            if "new_login" in update_dict:
                user.login = update_dict["new_login"]

            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def logout_user(
        self, user_id: str, current_user: dict, authorize: AuthJWT, redis: Redis, token_service: TokenService
    ):
        """Выход пользователя"""
        try:
            await token_service.get_token_from_redis(authorize, redis)
            if str(user_id) == current_user.get("user_id"):
                add_token_blacklist = await token_service.add_token_in_blacklist(authorize, redis)
            return {"message": "Вы вышли из профиля"}
        except AuthJWTException as e:
            raise HTTPException(status_code=401, detail=f"Ошибка выхода из профиля: {str(e)}")


def get_user_service(db: AsyncSession = Depends(get_session)) -> UserService:
    result = UserService(db)
    return result
