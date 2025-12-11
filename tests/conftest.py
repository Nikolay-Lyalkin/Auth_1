import asyncio
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest_asyncio
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import LoginHistory, Role, User
from src.schemas.users import TokenSchema, UserAuthSchema, UserCreateSchema


@pytest_asyncio.fixture(scope="function")
async def event_loop():
    """Event loop для асинхронных тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
def mock_db_session():
    """Фикстура мока сессии БД"""
    return AsyncMock(spec=AsyncSession)


@pytest_asyncio.fixture
def mock_role():
    """Фикстура мока роли"""
    role = MagicMock(spec=Role)
    role.id = uuid.uuid4()
    role.name = "user"
    role.description = "Regular user"
    role.created_at = datetime.utcnow()
    return role


@pytest_asyncio.fixture
def mock_user(mock_role):
    """Фикстура мока пользователя"""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.login = "test"
    user.password = "test"
    user.first_name = "Test"
    user.last_name = "Test"
    user.role_id = mock_role.id
    user.created_at = datetime.utcnow()

    user.check_password = Mock()
    return user


@pytest_asyncio.fixture
def mock_login_history(mock_user):
    """Фикстура мока истории авторизации"""
    history = MagicMock(spec=LoginHistory)
    history.id = uuid.uuid4()
    history.user_id = mock_user.id
    history.login_time = datetime.utcnow()
    history.ip_address = "127.0.0.1"
    history.user_agent = "Mozilla/5.0 (Test Agent)"
    history.device_type = "desktop"
    history.login_status = "success"
    return history


@pytest_asyncio.fixture
def mock_request():
    """Фикстура для мока Request"""
    request = MagicMock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.headers = {"user-agent": "test-agent"}
    return request


@pytest_asyncio.fixture
def mock_login_history_service():
    """Фикстура для мока LoginHistoryService"""
    service = Mock()
    service.create_login_history_from_request = AsyncMock()
    return service


@pytest_asyncio.fixture
def mock_token_service():
    """Фикстура TokenService"""
    mock_service = AsyncMock()
    mock_service.get_token_from_redis = AsyncMock(return_value=None)
    return mock_service


@pytest_asyncio.fixture
def user_create_data():
    """Фикстура данных для создания пользователя"""
    return UserCreateSchema(login="test", password="test", first_name="Test", last_name="Test")


@pytest_asyncio.fixture
def user_auth_data():
    """Фикстура данных для авторизации пользователя"""
    return UserAuthSchema(login="test", password="test")


@pytest_asyncio.fixture
def token():
    """Фикстура токена"""
    return TokenSchema(access_token="test", refresh_token="test")


@pytest_asyncio.fixture
def mock_authorize():
    """Фикстура для AuthJWT (fastapi-jwt-auth)"""
    mock = MagicMock()
    return mock


@pytest_asyncio.fixture
def mock_redis():
    """Фикстура для Redis (redis.asyncio)"""
    mock = AsyncMock()
    return mock.get
