from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from pydantic import EmailStr

from src.repository.contacts import ContactRepository
from src.schemas import ContactModel
from src.database.models import User


def _handle_integrity_error(e: IntegrityError):
    """
    Handle database integrity errors by raising an HTTP 400 exception.

    Args:
        e (IntegrityError): The raised SQLAlchemy integrity error.

    Raises:
        HTTPException: With 400 status and a data consistency message.
    """
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Data consistency error",
    )


class ContactService:
    """
    Service layer for managing contact operations.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the contact service with a database session.

        Args:
            db (AsyncSession): The SQLAlchemy async session.
        """
        self.repository = ContactRepository(db)

    async def create_contact(self, body: ContactModel, user: User):
        """
        Create a new contact for the given user.

        Args:
            body (ContactModel): The contact data to create.
            user (User): The owner of the contact.

        Returns:
            Contact: The created contact instance.

        Raises:
            HTTPException: If a database integrity error occurs.
        """
        try:
            return await self.repository.create_contact(body, user)
        except IntegrityError as e:
            await self.repository.db.rollback()
            _handle_integrity_error(e)

    async def get_contacts(self, skip: int, limit: int, user: User):
        """
        Retrieve a list of contacts with pagination.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.
            user (User): The owner of the contacts.

        Returns:
            List[Contact]: List of contact records.
        """
        return await self.repository.get_contacts(skip, limit, user)

    async def get_contact(self, contact_id: int, user: User):
        """
        Retrieve a contact by its ID.

        Args:
            contact_id (int): The contact's unique identifier.
            user (User): The owner of the contact.

        Returns:
            Contact | None: The contact if found, otherwise None.
        """
        return await self.repository.get_contact_by_id(contact_id, user)

    async def update_contact(self, contact_id: int, body: ContactModel, user: User):
        """
        Update an existing contact's information.

        Args:
            contact_id (int): The ID of the contact to update.
            body (ContactModel): The updated contact data.
            user (User): The owner of the contact.

        Returns:
            Contact: The updated contact instance.

        Raises:
            HTTPException: If a database integrity error occurs.
        """
        try:
            return await self.repository.update_contact(contact_id, body, user)
        except IntegrityError as e:
            await self.repository.db.rollback()
            _handle_integrity_error(e)

    async def delete_contact(self, contact_id: int, user: User):
        """
        Delete a contact by ID.

        Args:
            contact_id (int): The contact's unique identifier.
            user (User): The owner of the contact.

        Returns:
            Contact | None: The deleted contact if it existed, otherwise None.
        """
        return await self.repository.delete_contact(contact_id, user)

    async def search_contacts(
        self,
        user: User,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[EmailStr] = None,
    ):
        """
        Search for contacts based on first name, last name, or email.

        Args:
            user (User): The owner of the contacts.
            first_name (Optional[str], optional): Filter by first name.
            last_name (Optional[str], optional): Filter by last name.
            email (Optional[EmailStr], optional): Filter by email.

        Returns:
            List[Contact]: List of matched contacts.
        """
        return await self.repository.search_contacts(
            user=user, first_name=first_name, last_name=last_name, email=email
        )

    async def get_upcoming_birthdays(self, user: User):
        """
        Retrieve contacts with upcoming birthdays.

        Args:
            user (User): The owner of the contacts.

        Returns:
            List[Contact]: List of contacts with birthdays soon.
        """
        return await self.repository.get_upcoming_birthdays(user)
