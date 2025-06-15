from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.repository.users import UserRepository
from src.schemas import UserCreate


class UserService:
    """
    Service class for user-related operations.
    """
     
    def __init__(self, db: AsyncSession):
        """
        Initialize the UserService with a database session.

        Args:
            db (AsyncSession): SQLAlchemy asynchronous database session.
        """
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        """
        Create a new user and assign a Gravatar avatar if available.

        Args:
            body (UserCreate): Pydantic schema containing user creation data.

        Returns:
            User: The created user instance.
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int):
        """
        Retrieve a user by their ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            User | None: The user if found, otherwise None.
        """
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str):
        """
        Retrieve a user by their username.

        Args:
            username (str): The username to search for.

        Returns:
            User | None: The user if found, otherwise None.
        """
        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: str):
        """
        Retrieve a user by their email address.

        Args:
            email (str): The email to search for.

        Returns:
            User | None: The user if found, otherwise None.
        """
        return await self.repository.get_user_by_email(email)

    async def confirmed_email(self, email: str):
        """
        Mark a user's email as confirmed.

        Args:
            email (str): The user's email to confirm.

        Returns:
            User: The updated user instance with confirmed email.
        """
        return await self.repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str):
        """
        Update the avatar URL for a user.

        Args:
            email (str): The user's email.
            url (str): The new avatar URL.

        Returns:
            User: The updated user instance.
        """
        return await self.repository.update_avatar_url(email, url)
    
    async def reset_password(self, email: str, new_password: str):
        """
        Reset a user's password.

        Args:
            email (str): The user's email.
            new_password (str): The new password.

        Returns:
            User: The updated user instance with new password.
        """
        return await self.repository.reset_password(email, new_password)
