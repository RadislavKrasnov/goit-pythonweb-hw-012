import pytest
from unittest.mock import patch, AsyncMock
from io import BytesIO
from src.database.models import UserRole
from src.database.models import User
from tests.integration.conftest import TestingSessionLocal, get_token, client


@pytest.mark.asyncio
@patch("src.cache.cache_decorator.redis_client.set", new_callable=AsyncMock)
@patch("src.cache.cache_decorator.redis_client.get", new_callable=AsyncMock)
async def test_get_me(mock_get, mock_set, client, get_token):
    mock_get.return_value = None
    response = client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "agent007"
    assert data["email"] == "agent007@gmail.com"
    assert "hashed_password" not in data


@pytest.mark.asyncio
@patch("src.cache.cache_decorator.redis_client.set", new_callable=AsyncMock)
@patch("src.cache.cache_decorator.redis_client.get", new_callable=AsyncMock)
async def test_update_avatar_user(mock_get, mock_set, client, get_token):
    mock_get.return_value = None
    async with TestingSessionLocal() as session:
        user = await session.get(User, 1)
        user.role = UserRole.ADMIN
        await session.commit()

    dummy_avatar_url = "https://example.com/avatar.jpg"

    with patch(
        "src.api.users.UploadFileService.upload_file", return_value=dummy_avatar_url
    ):
        file_content = BytesIO(b"dummy image content")
        response = client.patch(
            "/api/users/avatar",
            headers={"Authorization": f"Bearer {get_token}"},
            files={"file": ("avatar.jpg", file_content, "image/jpeg")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["avatar"] == dummy_avatar_url
    assert data["role"] == "admin"
