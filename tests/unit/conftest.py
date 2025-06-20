import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User, Contact
from src.schemas import ContactModel
from fastapi import Request
from src.api.auth import Hash
from datetime import date


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
def contact_data():
    return ContactModel(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="12345678900",
        birthday=date.today(),
    )


@pytest.fixture
def contact():
    return Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="12345678900",
        birthday=date.today(),
    )


@pytest.fixture
def fake_request():
    req = MagicMock(spec=Request)
    req.base_url = "http://testserver"
    return req
