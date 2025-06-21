import pytest
from src.database.db import get_db
from tests.integration.conftest import client


@pytest.mark.asyncio
async def test_healthchecker_success(client):
    response = client.get("/api/healthchecker")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI!"}


@pytest.mark.asyncio
async def test_healthchecker_db_failure(client):
    async def broken_db():
        raise Exception("Simulated DB failure")

    client.app.dependency_overrides[get_db] = lambda: broken_db()

    response = client.get("/api/healthchecker")
    assert response.status_code == 500
    assert response.json()["detail"] == "Error connecting to the database"

    client.app.dependency_overrides.clear()
