from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from pydantic import EmailStr

from src.repository.contacts import ContactRepository
from src.schemas import ContactModel
from src.database.models import User


def _handle_integrity_error(e: IntegrityError):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Data consistency error",
    )


class ContactService:
    def __init__(self, db: AsyncSession):
        self.repository = ContactRepository(db)

    async def create_contact(self, body: ContactModel, user: User):
        try:
            return await self.repository.create_contact(body, user)
        except IntegrityError as e:
            await self.repository.db.rollback()
            _handle_integrity_error(e)

    async def get_contacts(self, skip: int, limit: int, user: User):
        return await self.repository.get_contacts(skip, limit, user)

    async def get_contact(self, contact_id: int, user: User):
        return await self.repository.get_contact_by_id(contact_id, user)

    async def update_contact(self, contact_id: int, body: ContactModel, user: User):
        try:
            return await self.repository.update_contact(contact_id, body, user)
        except IntegrityError as e:
            await self.repository.db.rollback()
            _handle_integrity_error(e)

    async def delete_contact(self, contact_id: int, user: User):
        return await self.repository.delete_contact(contact_id, user)

    async def search_contacts(
        self,
        user: User,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[EmailStr] = None,
    ):
        return await self.repository.search_contacts(
            user=user, first_name=first_name, last_name=last_name, email=email
        )

    async def get_upcoming_birthdays(self, user: User):
        return await self.repository.get_upcoming_birthdays(user)
