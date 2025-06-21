
# import pytest
# import pytest_asyncio
# from httpx import AsyncClient
# from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
# from sqlalchemy.pool import NullPool
# from fastapi import FastAPI

# from main import app
# from src.database.models import Base, User, UserRole
# from src.database.db import get_db
# from src.services.auth import create_access_token, Hash

# from unittest.mock import AsyncMock, patch
# from io import BytesIO
# from src.conf.config import settings
# from httpx._transports.asgi import ASGITransport


# engine = create_async_engine(settings.TEST_DB_URL, poolclass=NullPool, echo=True)
# TestingSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

# test_user = {
#     "username": "testuser",
#     "email": "testuser@example.com",
#     "password": "password123",
# }

# @pytest_asyncio.fixture
# async def get_token():
#     return await create_access_token(data={"sub": test_user["username"]})

# @pytest.fixture(scope="session", autouse=True)
# def initialize_test_db():
#     async def setup():
#         async with engine.begin() as conn:
#             await conn.run_sync(Base.metadata.drop_all)
#             await conn.run_sync(Base.metadata.create_all)

#         async with TestingSessionLocal() as session:
#             hashed_pw = Hash().get_password_hash(test_user["password"])
#             user = User(
#                 username=test_user["username"],
#                 email=test_user["email"],
#                 hashed_password=hashed_pw,
#                 avatar="https://example.com/avatar.jpg",
#                 confirmed=True,
#                 role="user",
#             )
#             session.add(user)
#             await session.commit()

#     import asyncio
#     asyncio.run(setup())

# @pytest_asyncio.fixture
# async def async_client():
#     async def override_get_db():
#         async with TestingSessionLocal() as session:
#             yield session

#     app.dependency_overrides[get_db] = override_get_db

#     transport = ASGITransport(app=app)
#     async with AsyncClient(transport=transport, base_url="http://test") as client:
#         yield client


# @pytest.mark.asyncio
# @patch("src.cache.cache_decorator.redis_client.get", new_callable=AsyncMock)
# @patch("src.cache.cache_decorator.redis_client.set", new_callable=AsyncMock)
# async def test_get_me(mock_set, mock_get, async_client, get_token):
#     mock_get.return_value = None  # simulate cache miss
#     response = await async_client.get(
#         "/api/users/me",
#         headers={"Authorization": f"Bearer {get_token}"}
#     )
#     assert response.status_code == 200


# @pytest.mark.asyncio
# @patch("src.cache.cache_decorator.redis_client.set", new_callable=AsyncMock)
# @patch("src.cache.cache_decorator.redis_client.get", new_callable=AsyncMock)
# async def test_update_avatar_user(mock_get, mock_set, async_client, get_token):
#     mock_get.return_value = None  # simulate cache miss

#     async with TestingSessionLocal() as session:
#         user = await session.get(User, 1)
#         user.role = UserRole.ADMIN
#         await session.commit()

#     dummy_avatar_url = "https://example.com/avatar.jpg"

#     with patch("src.api.users.UploadFileService.upload_file", return_value=dummy_avatar_url):
#         file_content = BytesIO(b"dummy image content")
#         response = await async_client.patch(
#             "/api/users/avatar",
#             headers={"Authorization": f"Bearer {get_token}"},
#             files={"file": ("avatar.jpg", file_content, "image/jpeg")},
#         )

#     assert response.status_code == 200
#     data = response.json()
#     assert data["avatar"] == dummy_avatar_url
#     assert data["role"] == "admin"

import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status
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
        "/api/users/me",
        headers={"Authorization": f"Bearer {get_token}"}
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

    with patch("src.api.users.UploadFileService.upload_file", return_value=dummy_avatar_url):
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
