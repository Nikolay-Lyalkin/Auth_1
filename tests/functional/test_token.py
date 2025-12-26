from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from async_fastapi_jwt_auth import AuthJWT

from src.services.token import TokenService


@pytest.mark.asyncio
async def test_get_current_user_required(mock_db_session):
    """Тест успешного получения текущего пользователя"""

    user_id = "123e4567-e89b-12d3-a456-426614174000"

    token_service = TokenService(mock_db_session)

    mock_authorize = MagicMock(spec=AuthJWT)

    mock_authorize.jwt_required = AsyncMock()
    mock_authorize.get_jwt_subject = AsyncMock(return_value=user_id)

    result = await token_service.get_current_user_required(mock_authorize, user_id)

    assert result == {"user_id": "123e4567-e89b-12d3-a456-426614174000", "authenticated": True}
    mock_authorize.jwt_required.assert_called_once()
    mock_authorize.get_jwt_subject.assert_called_once()


@pytest.mark.asyncio
async def test_generate_access_token(mock_db_session):
    """Тест успешной генерации access токена"""
    token_service = TokenService(mock_db_session)

    mock_authorize = MagicMock()
    mock_authorize.create_access_token = AsyncMock(return_value="mock.jwt.token.here")

    user_id = "123e4567-e89b-12d3-a456-426614174000"

    mock_user = MagicMock()
    mock_user.id = user_id

    mock_role = MagicMock()
    mock_role.name = "user"

    mock_user.role = mock_role

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = mock_user  # используем scalar_one, а не scalar_one_or_none

    mock_db_session.execute = AsyncMock(return_value=mock_result)

    result = await token_service.generate_access_token(user_id, mock_authorize)

    assert result == "mock.jwt.token.here"

    mock_authorize.create_access_token.assert_called_once_with(
        subject=user_id,
        user_claims={"user_id": user_id, "is_active": True, "token_type": "access", "role": "user"},
        expires_time=86400 * 7,
    )


@pytest.mark.asyncio
async def test_generate_refresh_token(mock_db_session):
    """Тест успешной генерации refresh токена"""

    token_service = TokenService(mock_db_session)

    mock_authorize = MagicMock()
    mock_authorize.create_refresh_token = AsyncMock(return_value="mock.refresh.token.here")

    user_id = "123e4567-e89b-12d3-a456-426614174000"

    mock_user = MagicMock()
    mock_user.id = user_id

    mock_role = MagicMock()
    mock_role.name = "user"

    mock_user.role = mock_role

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = mock_user

    mock_db_session.execute = AsyncMock(return_value=mock_result)

    result = await token_service.generate_refresh_token(user_id, mock_authorize)

    assert result == "mock.refresh.token.here"

    mock_authorize.create_refresh_token.assert_called_once_with(
        subject=user_id,
        user_claims={"user_id": user_id, "token_type": "refresh", "role": "user"},
        expires_time=86400 * 30,  # 30 дней
    )


@pytest.mark.asyncio
async def test_refresh_access_token(mock_db_session):
    """Тест успешного обновления access токена"""

    token_service = TokenService(mock_db_session)

    mock_authorize = MagicMock()

    mock_authorize.jwt_refresh_token_required = AsyncMock()
    mock_authorize.get_jwt_subject = AsyncMock(return_value="123e4567-e89b-12d3-a456-426614174000")
    mock_authorize.get_raw_jwt = AsyncMock(return_value={"token_type": "refresh"})

    with patch.object(
        token_service, "generate_access_token", AsyncMock(return_value="new.access.token")
    ) as mock_generate:
        result = await token_service.refresh_access_token(mock_authorize)

        assert result == "new.access.token"

        # Проверяем вызовы
        mock_authorize.jwt_refresh_token_required.assert_called_once()
        mock_authorize.get_jwt_subject.assert_called_once()
        mock_authorize.get_raw_jwt.assert_called_once()

        mock_generate.assert_called_once_with("123e4567-e89b-12d3-a456-426614174000", mock_authorize)


@pytest.mark.asyncio
async def test_add_token_in_blacklist_success(mock_db_session):
    """Тест успешного добавления токена в блэклист"""

    token_service = TokenService(mock_db_session)

    mock_authorize = MagicMock()
    mock_redis = AsyncMock()

    mock_jwt_data = {
        "jti": "unique-token-id-123",
        "exp": 1710000000,
        "sub": "123e4567-e89b-12d3-a456-426614174000",
        "role": "user",
    }

    mock_authorize.get_raw_jwt = AsyncMock(return_value=mock_jwt_data)

    mock_current_time = 1709999900

    with patch("src.services.token.datetime") as mock_datetime:
        mock_now = MagicMock()
        mock_now.timestamp.return_value = mock_current_time
        mock_datetime.now.return_value = mock_now

        await token_service.add_token_in_blacklist(mock_authorize, mock_redis)

        mock_authorize.get_raw_jwt.assert_called_once()

        expected_ttl = mock_jwt_data["exp"] - mock_current_time
        assert expected_ttl == 100

        mock_redis.setex.assert_called_once_with(mock_jwt_data["jti"], expected_ttl, mock_jwt_data["sub"])


@pytest.mark.asyncio
async def test_get_token_from_redis_token_not_in_blacklist(mock_db_session):
    """Тест когда токена нет в блэклисте"""

    token_service = TokenService(mock_db_session)

    mock_authorize = MagicMock()
    mock_redis = AsyncMock()

    mock_jwt_data = {"jti": "valid-token-id-123", "exp": 1710000000, "sub": "user123"}

    mock_authorize.get_raw_jwt = AsyncMock(return_value=mock_jwt_data)

    mock_redis.get = AsyncMock(return_value=0)

    result = await token_service.get_token_from_redis(mock_authorize, mock_redis)

    assert result is True
    mock_authorize.get_raw_jwt.assert_called_once()
    mock_redis.get.assert_called_once_with("valid-token-id-123")
