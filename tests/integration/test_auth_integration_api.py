import pytest
from unittest.mock import Mock
from sqlalchemy import select
from src.database.models import User
from tests.integration.conftest import TestingSessionLocal, client

user_data = {
    "username": "agent007",
    "email": "agent007@gmail.com",
    "password": "12345678",
}


def test_register_user(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)

    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201, response.text

    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hashed_password" not in data
    assert "avatar" in data


def test_register_duplicate_email(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)

    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 409
    assert response.json()["detail"] == "User with such email already exists"


def test_login_unconfirmed(client):
    client.post("/api/auth/register", json=user_data)

    response = client.post(
        "/api/auth/login",
        data={"username": user_data["username"], "password": user_data["password"]},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email is not verified"


@pytest.mark.asyncio
async def test_login_success(client):
    async with TestingSessionLocal() as session:
        user = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        user = user.scalar_one_or_none()
        if user:
            user.confirmed = True
            await session.commit()

    response = client.post(
        "/api/auth/login",
        data={"username": user_data["username"], "password": user_data["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_wrong_password(client):
    response = client.post(
        "/api/auth/login",
        data={"username": user_data["username"], "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect login or password"


def test_login_wrong_username(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "wronguser", "password": user_data["password"]},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect login or password"


def test_login_validation_error(client):
    response = client.post("/api/auth/login", data={"password": user_data["password"]})
    assert response.status_code == 422
    assert "detail" in response.json()
