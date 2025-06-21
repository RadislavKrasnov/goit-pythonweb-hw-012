import pytest
from unittest.mock import AsyncMock, patch, Mock
from fastapi import UploadFile
from src.api.users import me, update_avatar_user
from tests.unit.conftest import user, mock_session, fake_request
from io import BytesIO


@pytest.mark.asyncio
async def test_me_returns_user(fake_request, user):
    result = await me(fake_request, user)
    assert result == user


@pytest.mark.asyncio
@patch("src.api.users.UserService")
@patch("src.api.users.UploadFileService")
async def test_update_avatar_user(
    mock_upload_service_class, mock_user_service_class, user, mock_session
):
    mock_upload_service = Mock()
    mock_upload_service.upload_file.return_value = "http://example.com/avatar.jpg"
    mock_upload_service_class.return_value = mock_upload_service

    mock_user_service = AsyncMock()
    mock_user_service.update_avatar_url.return_value = user
    mock_user_service_class.return_value = mock_user_service

    file = UploadFile(filename="avatar.png", file=BytesIO(b"fake image data"))

    result = await update_avatar_user(file, user, mock_session)

    assert result == user
    mock_upload_service.upload_file.assert_called_once_with(file, user.username)
    mock_user_service.update_avatar_url.assert_called_once_with(
        user.email, "http://example.com/avatar.jpg"
    )
