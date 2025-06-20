import pytest
from unittest.mock import AsyncMock, patch
from fastapi import BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from src.api import auth
from src.schemas import (
    UserCreate,
    RequestEmail,
    TokenRefreshRequest,
    ResetPasswordRequest,
)
from tests.unit.conftest import fake_request, user, mock_session


@pytest.mark.asyncio
@patch("src.api.auth.UserService")
async def test_register_user(mock_user_service_class, fake_request, user, mock_session):
    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_email.return_value = None
    mock_user_service.get_user_by_username.return_value = None
    mock_user_service.create_user.return_value = user
    mock_user_service_class.return_value = mock_user_service

    user_data = UserCreate(
        username="testuser", email="test@example.com", password="pass"
    )
    background_tasks = BackgroundTasks()
    result = await auth.register_user(
        user_data, background_tasks, fake_request, mock_session
    )

    assert result.username == "testuser"
    assert len(background_tasks.tasks) == 1


@pytest.mark.asyncio
@patch("src.api.auth.UserService")
async def test_login_user_success(mock_user_service_class, user, mock_session):
    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_username.return_value = user
    mock_user_service_class.return_value = mock_user_service

    form_data = OAuth2PasswordRequestForm(
        username="testuser",
        password="password",
        scope="",
        grant_type="",
        client_id=None,
        client_secret=None,
    )
    result = await auth.login_user(form_data, mock_session)

    assert "access_token" in result
    assert "refresh_token" in result


@pytest.mark.asyncio
@patch("src.api.auth.get_email_from_token", return_value="test@example.com")
@patch("src.api.auth.UserService")
async def test_confirmed_email_success(mock_user_service_class, user, mock_session):
    user.confirmed = False

    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_email.return_value = user
    mock_user_service.confirmed_email.return_value = None
    mock_user_service_class.return_value = mock_user_service

    response = await auth.confirmed_email("token", mock_session)
    assert response == {"message": "Email is verified successfully"}


@pytest.mark.asyncio
@patch("src.api.auth.UserService")
async def test_request_email(mock_user_service_class, fake_request, user, mock_session):
    user.confirmed = False

    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_email.return_value = user
    mock_user_service_class.return_value = mock_user_service

    background_tasks = BackgroundTasks()
    body = RequestEmail(email="test@example.com")

    result = await auth.request_email(
        body, background_tasks, fake_request, mock_session
    )
    assert result == {"message": "Check your email for verification"}


@pytest.mark.asyncio
@patch("src.api.auth.verify_refresh_token")
async def test_new_token(mock_verify_refresh, user, mock_session):
    mock_verify_refresh.return_value = user

    request_data = TokenRefreshRequest(refresh_token="dummy_token")

    response = await auth.new_token(request_data, mock_session)
    assert "access_token" in response
    assert response["refresh_token"] == "dummy_token"


@pytest.mark.asyncio
@patch("src.api.auth.UserService")
async def test_reset_password_request(
    mock_user_service_class, fake_request, user, mock_session
):
    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_email.return_value = user
    mock_user_service_class.return_value = mock_user_service

    background_tasks = BackgroundTasks()
    body = RequestEmail(email="test@example.com")

    response = await auth.reset_password_request(
        body, background_tasks, fake_request, mock_session
    )
    assert response == {"message": "Reset link sent"}
    assert len(background_tasks.tasks) == 1


@pytest.mark.asyncio
@patch("src.api.auth.jwt.decode")
@patch("src.api.auth.UserService")
async def test_reset_password_success(
    mock_user_service_class, mock_jwt_decode, user, mock_session
):
    mock_jwt_decode.return_value = {
        "email": "test@example.com",
        "scope": "password_reset",
    }

    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_email.return_value = user
    mock_user_service.reset_password.return_value = None
    mock_user_service_class.return_value = mock_user_service

    body = ResetPasswordRequest(token="token", new_password="newpassword")

    result = await auth.reset_password(body, mock_session)
    assert result == {"message": "Password was reset"}
