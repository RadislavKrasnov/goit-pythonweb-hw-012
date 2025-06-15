from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Contact, User
from src.schemas import ContactModel
from datetime import date, timedelta
from pydantic import EmailStr


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(self, skip: int, limit: int, user: User) -> List[Contact]:
        stmt = (
            select(Contact)
            .filter_by(user_id=user.id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Optional[Contact]:
        stmt = select(Contact).where(Contact.id == contact_id, Contact.user_id == user.id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact:
        contact = Contact(**body.model_dump(exclude_unset=True), user_id=user.id)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(self, contact_id: int, body: ContactModel, user: User) -> Optional[Contact]:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, field, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Optional[Contact]:
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
