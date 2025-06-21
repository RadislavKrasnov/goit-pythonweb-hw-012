import pytest
from unittest.mock import AsyncMock, patch, Mock
from src.api.utils import healthchecker
from tests.unit.conftest import mock_session


@pytest.mark.asyncio
async def test_healthchecker_success(mock_session):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = 1

    mock_session.execute.return_value = mock_result

    response = await healthchecker(mock_session)
    assert response == {"message": "Welcome to FastAPI!"}


@pytest.mark.asyncio
async def test_healthchecker_no_result(mock_session):
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None

    mock_session.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(Exception) as exc:
        await healthchecker(mock_session)
    assert exc.value.status_code == 500
    assert exc.value.detail == "Error connecting to the database"
