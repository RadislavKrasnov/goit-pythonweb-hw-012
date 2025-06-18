import pytest
from unittest.mock import AsyncMock, MagicMock
from src.repository.users import UserRepository
from src.database.models import User
from src.schemas import UserCreate
from tests.unit.conftest import mock_session, user


@pytest.fixture
def user_repository(mock_session):
    return UserRepository(mock_session)


@pytest.mark.asyncio
async def test_get_user_by_id(user_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_id(1)

    assert result == user


@pytest.mark.asyncio
async def test_get_user_by_username(user_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_username("testuser")

    assert result == user


@pytest.mark.asyncio
async def test_get_user_by_email(user_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_email("test@example.com")

    assert result == user


@pytest.mark.asyncio
async def test_create_user(user_repository, mock_session):
    body = UserCreate(
        username="testuser", email="test@example.com", password="securepass"
    )
    avatar = "http://example.com/avatar.png"

    mock_user = User(
        id=1,
        username=body.username,
        email=body.email,
        hashed_password=body.password,
        avatar=avatar,
    )

    def add_side_effect(u):
        u.id = 1
        return None

    mock_session.add.side_effect = add_side_effect
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    result = await user_repository.create_user(body, avatar)

    assert isinstance(result, User)
    assert result.username == "testuser"
    assert result.email == "test@example.com"
    assert result.avatar == avatar


@pytest.mark.asyncio
async def test_confirmed_email(user_repository, mock_session, user):
    user.confirmed = False

    user_repository.get_user_by_email = AsyncMock(return_value=user)
    mock_session.commit = AsyncMock()

    await user_repository.confirmed_email(user.email)

    assert user.confirmed is True
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_avatar_url(user_repository, mock_session, user):
    user.avatar = None
    new_url = "http://example.com/new_avatar.png"

    user_repository.get_user_by_email = AsyncMock(return_value=user)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    result = await user_repository.update_avatar_url(user.email, new_url)

    assert result.avatar == new_url
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_reset_password(user_repository, mock_session, user):
    new_password = "new_hashed_pass"
    user_repository.get_user_by_email = AsyncMock(return_value=user)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    result = await user_repository.reset_password(user.email, new_password)

    assert result.hashed_password == new_password
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(user)
