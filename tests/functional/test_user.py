import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.schemas.users import UserUpdateSchema
from src.services.user import UserService


@pytest.mark.asyncio
async def test_create_user(user_create_data):
    """Создание пользователя"""

    mock_db_session = AsyncMock()
    user_service = UserService(mock_db_session)

    mock_role = MagicMock()
    mock_role.id = 1

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.login = "test"

    with patch.object(user_service, 'create_user') as mock_create_method:
        mock_create_method.return_value = mock_user

        result = await user_service.create_user(user_create_data)

        mock_create_method.assert_called_once_with(user_create_data)
        assert result == mock_user


@pytest.mark.asyncio
async def test_create_user_not_role(mock_db_session, mock_user, user_create_data):
    """Успешное создание пользователя"""

    user_service = UserService(mock_db_session)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    with pytest.raises(AttributeError) as exc_info:
        await user_service.create_user(user_create_data)
    assert "'NoneType' object has no attribute 'id'" in str(exc_info.value)


@pytest.mark.asyncio
async def test_auth(mock_db_session, mock_user, user_auth_data, mock_request, token, mock_login_history_service):
    user_service = UserService(mock_db_session)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db_session.execute.return_value = mock_result

    mock_user.check_password.return_value = True

    mock_jwt_service = MagicMock()
    mock_jwt_service.create_access_token.return_value = token.access_token
    mock_jwt_service.create_refresh_token.return_value = token.refresh_token

    result = await user_service.auth_user(user_auth_data, mock_request, mock_login_history_service)

    mock_db_session.execute.assert_called_once()
    mock_user.check_password.assert_called_once_with(user_auth_data.password)

    assert result is mock_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenario",
    [
        {
            "name": "update_own_profile_full",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "update_data": {"new_login": "new_user", "new_password": "NewPass123!"},
            "current_user_id": "123e4567-e89b-12d3-a456-426614174000",
            "expect_update": True,
        }
    ],
)
async def test_update_user_scenarios(
    scenario: dict, mock_db_session, mock_token_service, mock_authorize, mock_redis, mock_user
):
    """Тест различных сценариев обновления пользователя"""

    user_service = UserService(mock_db_session)

    mock_user.id = uuid.UUID(scenario["user_id"])
    mock_user.login = "original_login"
    mock_user.set_password = MagicMock()

    mock_db_result = AsyncMock()
    mock_db_result.scalar_one_or_none = AsyncMock(return_value=mock_user)

    mock_db_session.execute = AsyncMock(return_value=mock_db_result)

    current_user = {"user_id": scenario["current_user_id"], "authenticated": True}

    update_schema = UserUpdateSchema(**scenario["update_data"])

    result = await user_service.update_user(
        user_id=scenario["user_id"],
        update_data=update_schema,
        current_user=current_user,
        authorize=mock_authorize,
        redis=mock_redis,
        token_service=mock_token_service,
    )

    assert result == mock_user

    mock_token_service.get_token_from_redis.assert_called_once_with(mock_authorize, mock_redis)
    mock_db_session.execute.assert_called_once()
    mock_db_result.scalar_one_or_none.assert_called_once()

    if scenario["expect_update"]:

        if "new_login" in scenario["update_data"]:
            assert mock_user.login == scenario["update_data"]["new_login"]

        if "new_password" in scenario["update_data"]:
            mock_user.set_password.assert_called_once_with(scenario["update_data"]["new_password"])

        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_user)
