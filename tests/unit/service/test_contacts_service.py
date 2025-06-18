import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.exc import IntegrityError
from src.services.contacts import ContactService
from src.schemas import ContactModel
from src.database.models import User
from tests.unit.conftest import mock_session, user
from datetime import date


@pytest.fixture
def contact_service(mock_session):
    return ContactService(mock_session)


@pytest.fixture
def contact_data():
    return ContactModel(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="12345678900",
        birthday=date.today(),
    )


@pytest.mark.asyncio
async def test_create_contact_success(contact_service, user, contact_data):
    contact_service.repository.create_contact = AsyncMock(return_value=contact_data)
    result = await contact_service.create_contact(contact_data, user)
    assert result == contact_data
    contact_service.repository.create_contact.assert_awaited_once_with(
        contact_data, user
    )


@pytest.mark.asyncio
async def test_create_contact_integrity_error(contact_service, user, contact_data):
    contact_service.repository.create_contact = AsyncMock(
        side_effect=IntegrityError("mock", {}, None)
    )
    contact_service.repository.db.rollback = AsyncMock()

    with pytest.raises(Exception) as exc:
        await contact_service.create_contact(contact_data, user)

    contact_service.repository.db.rollback.assert_awaited_once()
    assert exc.type is not None
