from functools import wraps
from typing import Callable

from async_fastapi_jwt_auth import AuthJWT
from fastapi import Depends, status, HTTPException


def roles_required(roles_list: list[str]):
    """
    Декоратор для проверки ролей пользователя (версия с JWT claims)
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, authorize: AuthJWT = Depends(), **kwargs):
            try:

                # Проверяем JWT токен
                await authorize.jwt_required()

                # Получаем claims из токена
                jwt_data = await authorize.get_raw_jwt()

                # Проверяем наличие роли в claims
                user_role = jwt_data.get("role")
                if not user_role:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Роль не найдена в токене")

                # Проверяем разрешенные роли
                if user_role not in roles_list:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

                # Вызываем оригинальную функцию
                return await func(*args, authorize=authorize, **kwargs)

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Ошибка: {str(e)}")

        return wrapper

    return decorator
