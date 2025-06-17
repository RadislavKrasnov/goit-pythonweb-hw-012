import pytest
from jose import jwt, JWTError
from fastapi import HTTPException, status
from unittest.mock import patch, AsyncMock

from src.services.auth import (
    Hash,
    create_token,
    create_access_token,
    create_refresh_token,
    create_email_token,
    get_email_from_token,
    verify_refresh_token,
)
from src.database.models import User, UserRole
from src.conf.config import settings
from datetime import date, timedelta

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
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == "testuser"
    assert payload["token_type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


@pytest.mark.asyncio
async def test_create_access_token_default_expiry():
    data = {"sub": "testuser"}
    token = await create_access_token(data)
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == "testuser"
    assert payload["token_type"] == "access"


@pytest.mark.asyncio
async def test_create_refresh_token_custom_expiry():
    data = {"sub": "testuser"}
    token = await create_refresh_token(data, timedelta(minutes=5))
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == "testuser"
    assert payload["token_type"] == "refresh"
