from async_fastapi_jwt_auth import AuthJWT
from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.postgres import get_session
from src.models.user import Role
from src.schemas.user_roles import RoleCreateSchema, RoleInDBSchema
from src.services.token import security_jwt
from src.services.user_roles import roles_required

router = APIRouter()


@router.post("/role/create", response_model=RoleInDBSchema, status_code=status.HTTP_201_CREATED)
@roles_required(["superuser"])
async def create_role(
    role_create: RoleCreateSchema,
    db: AsyncSession = Depends(get_session),
    authorize: AuthJWT = Depends(),
    user: dict = Depends(security_jwt),
) -> RoleInDBSchema:
    """Создание роли"""
    role_dto = jsonable_encoder(role_create)
    role = Role(**role_dto)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role
