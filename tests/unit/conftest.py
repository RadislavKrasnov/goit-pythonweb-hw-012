import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User
from fastapi import Request
from src.api.auth import Hash


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        avatar="url",
        hashed_password=Hash().get_password_hash("password"),
        confirmed=True,
    )


@pytest.fixture
def fake_request():
    req = MagicMock(spec=Request)
    req.base_url = "http://testserver"
    return req
