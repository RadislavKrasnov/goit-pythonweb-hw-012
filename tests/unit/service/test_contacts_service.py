import pytest
from unittest.mock import AsyncMock
from sqlalchemy.exc import IntegrityError
from src.services.contacts import ContactService
from src.schemas import ContactModel
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


@pytest.mark.asyncio
async def test_get_contacts(contact_service, contact_data, user):
    contact_service.repository.get_contacts = AsyncMock(return_value=[contact_data])
    result = await contact_service.get_contacts(0, 10, user)
    assert result == [contact_data]


@pytest.mark.asyncio
async def test_get_contact(contact_service, contact_data, user):
    contact_service.repository.get_contact_by_id = AsyncMock(return_value=contact_data)
    result = await contact_service.get_contact(1, user)
    assert result == contact_data


@pytest.mark.asyncio
async def test_update_contact_success(contact_service, user, contact_data):
    contact_service.repository.update_contact = AsyncMock(return_value=contact_data)
    result = await contact_service.update_contact(1, contact_data, user)
    assert result == contact_data


@pytest.mark.asyncio
async def test_update_contact_integrity_error(contact_service, user, contact_data):
    contact_service.repository.update_contact = AsyncMock(
        side_effect=IntegrityError("mock", {}, None)
    )
    contact_service.repository.db.rollback = AsyncMock()

    with pytest.raises(Exception) as exc:
        await contact_service.update_contact(1, contact_data, user)

    contact_service.repository.db.rollback.assert_awaited_once()
    assert exc.type is not None


@pytest.mark.asyncio
async def test_delete_contact(contact_service, contact_data, user):
    contact_service.repository.delete_contact = AsyncMock(return_value=contact_data)
    result = await contact_service.delete_contact(1, user)
    assert result == contact_data


@pytest.mark.asyncio
async def test_search_contacts(contact_service, contact_data, user):
    contact_service.repository.search_contacts = AsyncMock(return_value=[contact_data])
    result = await contact_service.search_contacts(user, first_name="John")
    assert result == [contact_data]


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(contact_service, contact_data, user):
    contact_service.repository.get_upcoming_birthdays = AsyncMock(
        return_value=[contact_data]
    )
    result = await contact_service.get_upcoming_birthdays(user)
    assert result == [contact_data]
