from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.postgres import get_session
from src.models.user import Role
from src.schemas.user_roles import RoleCreateSchema, RoleInDBSchema

router = APIRouter()


@router.post("/role/create", response_model=RoleInDBSchema, status_code=status.HTTP_201_CREATED)
async def create_role(role_create: RoleCreateSchema, db: AsyncSession = Depends(get_session)) -> RoleInDBSchema:
    """Создание роли"""
    role_dto = jsonable_encoder(role_create)
    role = Role(**role_dto)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role
