from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Contact, User
from src.schemas import ContactModel
from datetime import date, timedelta
from pydantic import EmailStr


class ContactRepository:
    """Repository for managing Contact entities in the database."""

    def __init__(self, session: AsyncSession):
        """
        Initializes the repository with a given asynchronous database session.

        Args:
            session (AsyncSession): SQLAlchemy async session.
        """
        self.db = session

    async def get_contacts(self, skip: int, limit: int, user: User) -> List[Contact]:
        """
        Returns a paginated list of the user's contacts.

        Args:
            skip (int): Number of contacts to skip.
            limit (int): Maximum number of contacts to return.
            user (User): The authenticated user.

        Returns:
            List[Contact]: List of contact instances.
        """
        stmt = (
            select(Contact)
            .filter_by(user_id=user.id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Optional[Contact]:
        """
        Retrieves a contact by ID for the authenticated user.

        Args:
            contact_id (int): Contact ID.
            user (User): The authenticated user.

        Returns:
            Optional[Contact]: The contact if found, else None.
        """
        stmt = select(Contact).where(Contact.id == contact_id, Contact.user_id == user.id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact:
        """
        Creates a new contact for the authenticated user.

        Args:
            body (ContactModel): Contact data.
            user (User): The authenticated user.

        Returns:
            Contact: The created contact instance.
        """
        contact = Contact(**body.model_dump(exclude_unset=True), user_id=user.id)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(self, contact_id: int, body: ContactModel, user: User) -> Optional[Contact]:
        """
        Updates an existing contact for the authenticated user.

        Args:
            contact_id (int): Contact ID.
            body (ContactModel): Updated contact data.
            user (User): The authenticated user.

        Returns:
            Optional[Contact]: The updated contact, or None if not found.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, field, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        """
        Deletes a contact for the authenticated user.

        Args:
            contact_id (int): Contact ID.
            user (User): The authenticated user.

        Returns:
            Optional[Contact]: The deleted contact, or None if not found.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def search_contacts(
        self,
        user: User,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[EmailStr] = None,
    ) -> List[Contact]:
        """
        Searches for contacts based on first name, last name, or email.

        Args:
            user (User): The authenticated user.
            first_name (Optional[str], optional): First name query. Defaults to None.
            last_name (Optional[str], optional): Last name query. Defaults to None.
            email (Optional[EmailStr], optional): Email query. Defaults to None.

        Returns:
            List[Contact]: List of matching contacts.
        """
        stmt = select(Contact).where(Contact.user_id == user.id)
        if first_name:
            stmt = stmt.where(Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:
            stmt = stmt.where(Contact.last_name.ilike(f"%{last_name}%"))
        if email:
            stmt = stmt.where(Contact.email.ilike(f"%{email}%"))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_upcoming_birthdays(self, user: User) -> List[Contact]:
        """
        Retrieves contacts with birthdays in the next 7 days.

        Args:
            user (User): The authenticated user.

        Returns:
            List[Contact]: List of contacts with upcoming birthdays.
        """
        today = date.today()
        in_seven_days = today + timedelta(days=7)
        today_str = today.strftime("%m-%d")
        in_seven_days_str = in_seven_days.strftime("%m-%d")

        stmt = select(Contact).where(
            Contact.user_id == user.id,
            func.to_char(Contact.birthday, "MM-DD").between(today_str, in_seven_days_str)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
