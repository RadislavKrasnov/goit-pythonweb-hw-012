import pytest
from unittest.mock import AsyncMock, MagicMock
from src.database.models import Contact
from src.repository.contacts import ContactRepository
from tests.unit.conftest import mock_session, user, contact, contact_data


@pytest.fixture
def contact_repository(mock_session):
    return ContactRepository(mock_session)


@pytest.mark.asyncio
async def test_get_contacts(contact_repository, mock_session, user, contact):
    contact.user_id = user.id
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [contact]
    mock_session.execute = AsyncMock(return_value=mock_result)

    contacts = await contact_repository.get_contacts(skip=0, limit=10, user=user)

    assert len(contacts) == 1
    assert contacts[0].first_name == "John"


@pytest.mark.asyncio
async def test_get_contact_by_id(contact_repository, mock_session, user, contact):
    contact.user_id = user.id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    contact = await contact_repository.get_contact_by_id(contact_id=1, user=user)

    assert contact is not None
    assert contact.id == 1


@pytest.mark.asyncio
async def test_create_contact(contact_repository, mock_session, user, contact_data):
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    contact = await contact_repository.create_contact(body=contact_data, user=user)

    assert isinstance(contact, Contact)
    assert contact.first_name == "John"
    mock_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_update_contact_found(
    contact_repository, mock_session, user, contact, contact_data
):
    contact.user_id = user.id
    existing_contact = contact
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    updated_contact = await contact_repository.update_contact(
        contact_id=1, body=contact_data, user=user
    )

    assert updated_contact is not None
    assert updated_contact.first_name == "John"
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_contact_not_found(
    contact_repository, mock_session, user, contact_data
):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    updated_contact = await contact_repository.update_contact(
        contact_id=999,
        body=contact_data,
        user=user,
    )

    assert updated_contact is None


@pytest.mark.asyncio
async def test_delete_contact_found(contact_repository, mock_session, user, contact):
    contact.user_id = user.id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    deleted = await contact_repository.delete_contact(contact_id=1, user=user)

    assert deleted is not None
    mock_session.delete.assert_awaited_once_with(contact)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_contact_not_found(contact_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    deleted = await contact_repository.delete_contact(contact_id=1, user=user)

    assert deleted is None
    mock_session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_search_contacts(contact_repository, mock_session, user, contact):
    contact.user_id = user.id
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [contact]
    mock_session.execute = AsyncMock(return_value=mock_result)

    results = await contact_repository.search_contacts(user=user, first_name="John")

    assert len(results) == 1
    assert results[0].first_name == "John"


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(contact_repository, mock_session, user, contact):
    contact.user_id = user.id
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [contact]
    mock_session.execute = AsyncMock(return_value=mock_result)

    results = await contact_repository.get_upcoming_birthdays(user=user)

    assert isinstance(results, list)
    assert results[0].first_name == "John"
