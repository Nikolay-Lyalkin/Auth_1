from typing import Annotated

from async_fastapi_jwt_auth import AuthJWT
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis

from exceptions import UserNotFound, UserInDB
from src.db.redis_db import get_redis
from src.schemas.users import (
    TokenSchema,
    UserAuthSchema,
    UserCreateSchema,
    UserInDBSchema,
    UserUpdateSchema,
    UserSchema,
    AuthResponse,
)
from src.services.login_history import LoginHistoryService, get_login_history
from src.services.token import TokenService, get_token_service, security_jwt
from src.services.user import UserService, get_user_service

router = APIRouter()


@router.post("/signup", response_model=UserInDBSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreateSchema, user_service: Annotated[UserService, Depends(get_user_service)]
) -> UserInDBSchema:
    try:
        user = await user_service.create_user(user_create)
    except UserInDB as ex:
        raise HTTPException(status_code=404, detail=ex.detail)
    return user


@router.post("/auth", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def auth_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    login_history_service: Annotated[LoginHistoryService, Depends(get_login_history)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    user_auth: UserAuthSchema,
    request: Request,
    authorize: AuthJWT = Depends(),
):
    try:
        user_orm = await user_service.auth_user(user_auth, request, login_history_service)
    except UserNotFound as ex:
        raise HTTPException(status_code=404, detail=ex.detail)
    access_token = await token_service.generate_access_token(str(user_orm.id), authorize)
    refresh_token = await token_service.generate_refresh_token(str(user_orm.id), authorize)
    token = TokenSchema(access_token=access_token, refresh_token=refresh_token)
    user = UserSchema.from_orm(user_orm)
    return AuthResponse(token=token, user=user)


@router.patch("/{user_id}/update", response_model=UserInDBSchema, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: str,
    update_data: UserUpdateSchema,
    user_service: Annotated[UserService, Depends(get_user_service)],
    authorize: AuthJWT = Depends(),
    token_service: TokenService = Depends(get_token_service),
    redis: Redis = Depends(get_redis),
    user: dict = Depends(security_jwt),
):
    current_user = await token_service.get_current_user_required(authorize, user_id)
    return await user_service.update_user(user_id, update_data, current_user, authorize, redis, token_service)


@router.post("/{user_id}/logout", status_code=status.HTTP_200_OK)
async def logout_user(
    user_id: str,
    user_service: Annotated[UserService, Depends(get_user_service)],
    token_service: TokenService = Depends(get_token_service),
    authorize: AuthJWT = Depends(),
    redis: Redis = Depends(get_redis),
    user: dict = Depends(security_jwt),
) -> dict:
    current_user = await token_service.get_current_user_required(authorize, user_id)
    return await user_service.logout_user(user_id, current_user, authorize, redis, token_service)


@router.get("/{user_id}/login_history", status_code=status.HTTP_200_OK)
async def login_history(
    user_id: str,
    token_service: Annotated[TokenService, Depends(get_token_service)],
    authorize: AuthJWT = Depends(),
    redis: Redis = Depends(get_redis),
    login_history_service: LoginHistoryService = Depends(get_login_history),
    user: dict = Depends(security_jwt),
):
    await token_service.get_current_user_required(authorize, user_id)
    history = await login_history_service.get_login_history(user_id, token_service, authorize, redis)
    return history


@router.post("/auth/yandex", response_class=RedirectResponse)
async def yandex_auth(user_service: Annotated[UserService, Depends(get_user_service)]):
    redirect_url = await user_service.get_yandex_redirect_url()
    return RedirectResponse(redirect_url)


@router.get("/auth/yandex/callback")
async def yandex_auth_callback(code: str, user_service: Annotated[UserService, Depends(get_user_service)]):
    user_info = await user_service.get_user_info(code)
    return user_info
