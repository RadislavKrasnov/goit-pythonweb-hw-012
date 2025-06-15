from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from src.database.db import get_db
from src.database.models import User
from src.schemas import ContactModel, ContactResponse
from src.services.contacts import ContactService
from src.services.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=List[ContactResponse])
async def read_contacts(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retrieve a list of contacts for the authenticated user.

    Args:
        skip (int): Number of records to skip.
        limit (int): Maximum number of contacts to return.
        db (AsyncSession): Database session.
        user (User): Currently authenticated user.

    Returns:
        List[ContactResponse]: List of user's contacts.
    """
    service = ContactService(db)
    return await service.get_contacts(skip, limit, user)


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retrieve a specific contact by ID.

    Args:
        contact_id (int): ID of the contact to retrieve.
        db (AsyncSession): Database session.
        user (User): Currently authenticated user.

    Returns:
        ContactResponse: Contact details.

    Raises:
        HTTPException: If contact is not found.
    """
    service = ContactService(db)
    contact = await service.get_contact(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactModel,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Create a new contact for the authenticated user.

    Args:
        body (ContactModel): Contact data to create.
        db (AsyncSession): Database session.
        user (User): Currently authenticated user.

    Returns:
        ContactResponse: The created contact.
    """
    service = ContactService(db)
    return await service.create_contact(body, user)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    body: ContactModel,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Update an existing contact by ID.

    Args:
        contact_id (int): ID of the contact to update.
        body (ContactModel): Updated contact data.
        db (AsyncSession): Database session.
        user (User): Currently authenticated user.

    Returns:
        ContactResponse: The updated contact.

    Raises:
        HTTPException: If contact is not found.
    """
    service = ContactService(db)
    contact = await service.update_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.delete("/{contact_id}", response_model=ContactResponse)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Delete a contact by ID.

    Args:
        contact_id (int): ID of the contact to delete.
        db (AsyncSession): Database session.
        user (User): Currently authenticated user.

    Returns:
        ContactResponse: The deleted contact.

    Raises:
        HTTPException: If contact is not found.
    """
    service = ContactService(db)
    contact = await service.delete_contact(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.get("/search/", response_model=List[ContactResponse])
async def search_contacts(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[EmailStr] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Search contacts by first name, last name, or email.

    Args:
        first_name (Optional[str]): First name to search for.
        last_name (Optional[str]): Last name to search for.
        email (Optional[EmailStr]): Email to search for.
        db (AsyncSession): Database session.
        user (User): Currently authenticated user.

    Returns:
        List[ContactResponse]: List of contacts matching the search criteria.
    """
    service = ContactService(db)
    return await service.search_contacts(
        user=user, first_name=first_name, last_name=last_name, email=email
    )


@router.get("/upcoming_birthdays/", response_model=List[ContactResponse])
async def upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retrieve contacts with upcoming birthdays within the next 7 days.

    Args:
        db (AsyncSession): Database session.
        user (User): Currently authenticated user.

    Returns:
        List[ContactResponse]: Contacts with upcoming birthdays.
    """
    service = ContactService(db)
    return await service.get_upcoming_birthdays(user)
