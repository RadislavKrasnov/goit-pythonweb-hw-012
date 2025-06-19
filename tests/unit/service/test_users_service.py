import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.users import UserService
from src.schemas import UserCreate
from src.database.models import User
from tests.unit.conftest import mock_session, user


@pytest.fixture
def user_create():
    return UserCreate(
        username="testuser", email="test@example.com", password="hashedpass"
    )


@pytest.fixture
def user_service(mock_session):
    return UserService(mock_session)


@pytest.mark.asyncio
@patch("src.services.users.Gravatar")
async def test_create_user_with_gravatar(
    mock_gravatar_class, user_service, user_create
):
    mock_gravatar = MagicMock()
    mock_gravatar.get_image.return_value = "https://gravatar.com/avatar.png"
    mock_gravatar_class.return_value = mock_gravatar

    user_service.repository.create_user = AsyncMock(
        return_value=User(username="testuser")
    )

    user = await user_service.create_user(user_create)

    mock_gravatar_class.assert_called_once_with("test@example.com")
    mock_gravatar.get_image.assert_called_once()
    user_service.repository.create_user.assert_awaited_once_with(
        user_create, "https://gravatar.com/avatar.png"
    )
    assert user.username == "testuser"


@pytest.mark.asyncio
@patch("src.services.users.Gravatar", side_effect=Exception("Gravatar error"))
async def test_create_user_gravatar_exception(
    mock_gravatar_class, user_service, user_create
):
    user_service.repository.create_user = AsyncMock(
        return_value=User(username="testuser")
    )

    user = await user_service.create_user(user_create)

    mock_gravatar_class.assert_called_once_with("test@example.com")
    user_service.repository.create_user.assert_awaited_once_with(user_create, None)
    assert user.username == "testuser"


@pytest.mark.asyncio
async def test_get_user_by_id(user_service, user):
    user_service.repository.get_user_by_id = AsyncMock(return_value=user)

    user = await user_service.get_user_by_id(1)

    user_service.repository.get_user_by_id.assert_awaited_once_with(1)
    assert user.username == "testuser"


@pytest.mark.asyncio
async def test_get_user_by_username(user_service, user):
    user_service.repository.get_user_by_username = AsyncMock(return_value=user)

    user = await user_service.get_user_by_username("testuser")

    user_service.repository.get_user_by_username.assert_awaited_once_with("testuser")
    assert user.username == "testuser"


@pytest.mark.asyncio
async def test_get_user_by_email(user_service, user):
    user_service.repository.get_user_by_email = AsyncMock(return_value=user)

    user = await user_service.get_user_by_email("test@example.com")

    user_service.repository.get_user_by_email.assert_awaited_once_with(
        "test@example.com"
    )
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_confirmed_email(user_service):
    user_service.repository.confirmed_email = AsyncMock(return_value=None)

    result = await user_service.confirmed_email("test@example.com")

    user_service.repository.confirmed_email.assert_awaited_once_with("test@example.com")
    assert result is None


@pytest.mark.asyncio
async def test_update_avatar_url(user_service, user):
    user_service.repository.update_avatar_url = AsyncMock(return_value=user)

    user = await user_service.update_avatar_url("test@example.com", "url")

    user_service.repository.update_avatar_url.assert_awaited_once_with(
        "test@example.com", "url"
    )
    assert user.avatar == "url"


@pytest.mark.asyncio
async def test_reset_password(user_service, user):
    user_service.repository.reset_password = AsyncMock(return_value=user)

    user = await user_service.reset_password("test@example.com", "newpass")

    user_service.repository.reset_password.assert_awaited_once_with(
        "test@example.com", "newpass"
    )
    assert user.username == "testuser"
