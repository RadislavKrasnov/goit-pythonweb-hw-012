import pytest
from unittest.mock import AsyncMock, patch
from src.api.contants import (
    read_contacts,
    read_contact,
    create_contact,
    update_contact,
    delete_contact,
    search_contacts,
    upcoming_birthdays,
)
from tests.unit.conftest import user, mock_session, contact, contact_data


@pytest.mark.asyncio
@patch("src.api.contants.ContactService")
async def test_read_contacts(mock_service_class, user, mock_session, contact):
    mock_service = AsyncMock()
    mock_service.get_contacts.return_value = [contact]
    mock_service_class.return_value = mock_service

    result = await read_contacts(0, 10, mock_session, user)

    assert result == [contact]


@pytest.mark.asyncio
@patch("src.api.contants.ContactService")
async def test_read_contact_found(mock_service_class, user, mock_session, contact):
    mock_service = AsyncMock()
    mock_service.get_contact.return_value = contact
    mock_service_class.return_value = mock_service

    result = await read_contact(1, mock_session, user)
    assert result == contact


@pytest.mark.asyncio
@patch("src.api.contants.ContactService")
async def test_read_contact_not_found(mock_service_class, user, mock_session):
    mock_service = AsyncMock()
    mock_service.get_contact.return_value = None
    mock_service_class.return_value = mock_service

    with pytest.raises(Exception) as exc:
        await read_contact(999, mock_session, user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
@patch("src.api.contants.ContactService")
async def test_create_contact(
    mock_service_class, user, mock_session, contact, contact_data
):
    mock_service = AsyncMock()
    mock_service.create_contact.return_value = contact
    mock_service_class.return_value = mock_service

    result = await create_contact(contact_data, mock_session, user)
    assert result == contact


@pytest.mark.asyncio
@patch("src.api.contants.ContactService")
async def test_update_contact_found(
    mock_service_class, user, mock_session, contact, contact_data
):
    mock_service = AsyncMock()
    mock_service.update_contact.return_value = contact
    mock_service_class.return_value = mock_service

    body = contact_data
    result = await update_contact(1, body, mock_session, user)
    assert result == contact


@pytest.mark.asyncio
@patch("src.api.contants.ContactService")
async def test_update_contact_not_found(
    mock_service_class, user, mock_session, contact_data
):
    mock_service = AsyncMock()
    mock_service.update_contact.return_value = None
    mock_service_class.return_value = mock_service

    body = contact_data
    with pytest.raises(Exception) as exc:
        await update_contact(999, body, mock_session, user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
@patch("src.api.contants.ContactService")
async def test_delete_contact_found(mock_service_class, user, mock_session, contact):
    mock_service = AsyncMock()
    mock_service.delete_contact.return_value = contact
    mock_service_class.return_value = mock_service

    result = await delete_contact(1, mock_session, user)
    assert result == contact


@pytest.mark.asyncio
@patch("src.api.contants.ContactService")
async def test_delete_contact_not_found(mock_service_class, user, mock_session):
    mock_service = AsyncMock()
    mock_service.delete_contact.return_value = None
    mock_service_class.return_value = mock_service

    with pytest.raises(Exception) as exc:
        await delete_contact(999, mock_session, user)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
@patch("src.api.contants.ContactService")
async def test_search_contacts(mock_service_class, user, mock_session, contact):
    mock_service = AsyncMock()
    mock_service.search_contacts.return_value = [contact]
    mock_service_class.return_value = mock_service

    result = await search_contacts(
        first_name="John", last_name=None, email=None, db=mock_session, user=user
    )
    assert result == [contact]


@pytest.mark.asyncio
@patch("src.api.contants.ContactService")
async def test_upcoming_birthdays(mock_service_class, user, mock_session, contact):
    mock_service = AsyncMock()
    mock_service.get_upcoming_birthdays.return_value = [contact]
    mock_service_class.return_value = mock_service

    result = await upcoming_birthdays(mock_session, user)
    assert result == [contact]
