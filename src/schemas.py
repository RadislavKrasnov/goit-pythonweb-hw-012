from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import date
from typing import Optional
from src.database.models import UserRole

class ContactModel(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_info: Optional[str] = None


class ContactResponse(ContactModel):
    id: int

    model_config = ConfigDict(from_attributes=True)

class User(BaseModel):
    id: int
    username: str
    email: str
    avatar: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[UserRole] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class RequestEmail(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
