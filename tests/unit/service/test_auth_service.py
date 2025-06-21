import pytest
from jose import jwt
from fastapi import HTTPException, status
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.auth import generate_reset_token
from src.services.auth import (
    Hash,
    create_token,
    create_access_token,
    create_refresh_token,
    create_email_token,
    get_email_from_token,
    verify_refresh_token,
    get_current_user,
    get_current_admin_user,
)
from src.database.models import User, UserRole
from src.conf.config import settings
from datetime import timedelta
from tests.unit.conftest import mock_session, user


def test_hash_password_and_verify():
    password = "secret123"
    hasher = Hash()
    hashed = hasher.get_password_hash(password)
    assert hasher.verify_password(password, hashed) is True
    assert hasher.verify_password("wrong", hashed) is False


def test_create_token_contains_expected_claims():
    data = {"sub": "testuser"}
    expires = 3600
    token = create_token(data, timedelta(seconds=expires), "access")
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert payload["sub"] == "testuser"
    assert payload["token_type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


@pytest.mark.asyncio
async def test_create_access_token_default_expiry():
    data = {"sub": "testuser"}
    token = await create_access_token(data)
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert payload["sub"] == "testuser"
    assert payload["token_type"] == "access"


@pytest.mark.asyncio
async def test_create_refresh_token_custom_expiry():
    data = {"sub": "testuser"}
    token = await create_refresh_token(data, timedelta(minutes=5))
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert payload["sub"] == "testuser"
    assert payload["token_type"] == "refresh"


def test_create_email_token_contains_email():
    data = {"sub": "test@example.com"}
    token = create_email_token(data)
    decoded = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert decoded["sub"] == "test@example.com"
    assert "exp" in decoded
    assert "iat" in decoded


@pytest.mark.asyncio
async def test_get_email_from_token_valid():
    token = jwt.encode(
        {"sub": "email@example.com"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    email = await get_email_from_token(token)
    assert email == "email@example.com"


@pytest.mark.asyncio
async def test_get_email_from_token_invalid():
    with pytest.raises(HTTPException) as exc:
        await get_email_from_token("invalid.token.here")
    assert exc.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_verify_refresh_token_valid_user(mock_session):
    refresh_token = jwt.encode(
        {"sub": "testuser", "token_type": "refresh"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    mock_user = User(username="testuser", refresh_token=refresh_token)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    user = await verify_refresh_token(refresh_token, mock_session)
    assert user.username == "testuser"


@pytest.mark.asyncio
async def test_verify_refresh_token_invalid_token_type(mock_session):
    token = jwt.encode(
        {"sub": "testuser", "token_type": "access"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    user = await verify_refresh_token(token, mock_session)
    assert user is None


@pytest.mark.asyncio
async def test_verify_refresh_token_invalid_token(mock_session):
    user = await verify_refresh_token("bad.token.string", mock_session)
    assert user is None


@pytest.mark.asyncio
async def test_generate_reset_token_contains_email():
    token = await generate_reset_token("user@example.com")
    decoded = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert decoded["email"] == "user@example.com"
    assert decoded["scope"] == "password_reset"


@pytest.mark.asyncio
@patch("src.cache.cache_decorator.redis_client.set", new_callable=AsyncMock)
@patch("src.cache.cache_decorator.redis_client.get", new_callable=AsyncMock)
@patch("src.services.auth.UserService")
@patch("src.services.auth.jwt.decode")
async def test_get_current_user_success(
    mock_jwt_decode, mock_user_service_class, mock_get, mock_set, mock_session, user
):
    mock_get.return_value = None
    mock_jwt_decode.return_value = {"sub": "testuser"}

    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_username.return_value = user
    mock_user_service_class.return_value = mock_user_service

    token = jwt.encode(
        {"sub": "testuser"}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    user = await get_current_user(token=token, db=mock_session)

    assert user.username == "testuser"


def test_get_current_admin_user_success(user):
    user.role = UserRole.ADMIN
    result = get_current_admin_user(current_user=user)
    assert result == user


def test_get_current_admin_user_forbidden(user):
    user.role = UserRole.USER

    with pytest.raises(HTTPException) as exc:
        get_current_admin_user(current_user=user)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
