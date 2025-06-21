import pytest
from datetime import date, timedelta
from tests.integration.conftest import client, get_token


contact = {
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice@example.com",
    "phone_number": "+1234567890",
    "birthday": str(date.today() + timedelta(days=3)),
    "additional_info": "Friend from college",
}


@pytest.mark.asyncio
async def test_create_contact(client, get_token):
    response = client.post(
        "/api/contacts/", headers={"Authorization": f"Bearer {get_token}"}, json=contact
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["first_name"] == contact["first_name"]
    assert data["email"] == contact["email"]


@pytest.mark.asyncio
async def test_read_contacts(client, get_token):
    response = client.get(
        "/api/contacts/", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(
        contact_response["email"] == contact["email"] for contact_response in data
    )


@pytest.mark.asyncio
async def test_get_contact_by_id(client, get_token):
    response = client.get(
        "/api/contacts/", headers={"Authorization": f"Bearer {get_token}"}
    )
    contact_id = response.json()[0]["id"]

    response = client.get(
        f"/api/contacts/{contact_id}", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == contact_id


@pytest.mark.asyncio
async def test_update_contact(client, get_token):
    updated_data = contact.copy()
    updated_data["first_name"] = "UpdatedName"

    response = client.get(
        "/api/contacts/", headers={"Authorization": f"Bearer {get_token}"}
    )
    contact_id = response.json()[0]["id"]

    response = client.put(
        f"/api/contacts/{contact_id}",
        headers={"Authorization": f"Bearer {get_token}"},
        json=updated_data,
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "UpdatedName"


@pytest.mark.asyncio
async def test_search_contacts(client, get_token):
    response = client.get(
        f"/api/contacts/search/?email={contact['email']}",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(
        contact_response["email"] == contact["email"] for contact_response in data
    )


@pytest.mark.asyncio
async def test_upcoming_birthdays(client, get_token):
    client.post(
        "/api/contacts/", headers={"Authorization": f"Bearer {get_token}"}, json=contact
    )
    response = client.get(
        "/api/contacts/upcoming_birthdays/",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert any(
        contact_response["email"] == contact["email"] for contact_response in data
    )
    assert all(
        date.fromisoformat(c["birthday"]) <= date.today() + timedelta(days=7)
        for c in data
    )


@pytest.mark.asyncio
async def test_delete_contact(client, get_token):
    response = client.get(
        "/api/contacts/", headers={"Authorization": f"Bearer {get_token}"}
    )
    contact_id = response.json()[0]["id"]

    response = client.delete(
        f"/api/contacts/{contact_id}", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == contact_id
