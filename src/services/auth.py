from datetime import datetime, timedelta, UTC
from typing import Optional, Literal
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from jose import JWTError, jwt
from src.database.db import get_db
from src.conf.config import settings
from src.services.users import UserService
from src.database.models import User
from src.cache.cache_decorator import redis_cache
from pydantic import EmailStr
from src.database.models import UserRole


class Hash:
    """Utility class for hashing and verifying passwords using bcrypt."""

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        """
        Verifies a plain password against its hashed version.

        Args:
            plain_password (str): The plaintext password.
            hashed_password (str): The hashed password.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Hashes a plain password.

        Args:
            password (str): The password to hash.

        Returns:
            str: The hashed password.
        """
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_token(
    data: dict, expires_delta: timedelta, token_type: Literal["access", "refresh"]
):
    """
    Creates a JWT token.

    Args:
        data (dict): Data to encode in the token.
        expires_delta (timedelta): Token expiration duration.
        token_type (Literal["access", "refresh"]): The type of token being created.

    Returns:
        str: Encoded JWT token.
    """
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def create_access_token(data: dict, expires_delta: Optional[float] = None):
    """
    Creates an access token.

    Args:
        data (dict): Data to include in the token.
        expires_delta (Optional[float], optional): Optional expiration override. Defaults to settings.

    Returns:
        str: JWT access token.
    """
    if expires_delta:
        access_token = create_token(data, expires_delta, "access")
    else:
        access_token = create_token(
            data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), "access"
        )
    return access_token


async def create_refresh_token(data: dict, expires_delta: Optional[float] = None):
    """
    Creates a refresh token.

    Args:
        data (dict): Data to include in the token.
        expires_delta (Optional[float], optional): Optional expiration override. Defaults to settings.

    Returns:
        str: JWT refresh token.
    """
    if expires_delta:
        refresh_token = create_token(data, expires_delta, "refresh")
    else:
        refresh_token = create_token(
            data, timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES), "refresh"
        )
    return refresh_token


def user_cache_key(token: str, *args, **kwargs):
    """
    Builds a cache key based on the JWT token.

    Args:
        token (str): The JWT token.

    Returns:
        str: The cache key.
    """
    return f"user({token})"


@redis_cache(key_builder=user_cache_key, expire=600)
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """
    Retrieves the current user from the token, using caching.

    Args:
        token (str): JWT token from OAuth2.
        db (Session): SQLAlchemy database session.

    Raises:
        HTTPException: If the token is invalid or user not found.

    Returns:
        User: Authenticated user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload["sub"]
        if username is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """
    Ensures the current user is an admin.

    Args:
        current_user (User): The currently authenticated user.

    Raises:
        HTTPException: If user is not an admin.

    Returns:
        User: The admin user.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient access rights"
        )
    return current_user


def create_email_token(data: dict):
    """
    Creates a JWT token for email confirmation.

    Args:
        data (dict): Data to encode.

    Returns:
        str: Encoded email confirmation token.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str):
    """
    Extracts email from a confirmation token.

    Args:
        token (str): Email confirmation token.

    Raises:
        HTTPException: If token is invalid or expired.

    Returns:
        EmailStr: Email extracted from token.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Невірний токен для перевірки електронної пошти",
        )


async def verify_refresh_token(refresh_token: str, db: Session):
    """
    Verifies and returns a user from a refresh token.

    Args:
        refresh_token (str): The refresh token to verify.
        db (Session): SQLAlchemy session.

    Returns:
        Optional[User]: The user if valid, otherwise None.
    """
    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type")
        if username is None or token_type != "refresh":
            return None
        result = await db.execute(
            select(User).where(
                User.username == username, User.refresh_token == refresh_token
            )
        )
        user = result.scalar_one_or_none()
        return user
    except JWTError:
        return None


async def generate_reset_token(email: EmailStr):
    """
    Generates a token for resetting a user's password.

    Args:
        email (EmailStr): Email of the user requesting the reset.

    Returns:
        str: Encoded reset token.
    """
    payload = {
        "email": email,
        "exp": datetime.now() + timedelta(minutes=30),
        "scope": "password_reset",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
