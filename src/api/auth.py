from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from src.services.auth import generate_reset_token
from jose import JWTError, jwt
from src.schemas import (
    UserCreate,
    Token,
    User,
    RequestEmail,
    TokenRefreshRequest,
    ResetPasswordRequest,
)
from src.services.auth import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    Hash,
    get_email_from_token,
)
from src.services.users import UserService
from src.services.email import send_email, send_password_reset_email
from src.database.db import get_db
from src.conf.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Register a new user and send an email verification link.

    Args:
        user_data (UserCreate): User registration information.
        background_tasks (BackgroundTasks): Background task handler to send emails.
        request (Request): HTTP request object for URL generation.
        db (Session): SQLAlchemy session for database interaction.

    Returns:
        User: The newly created user object.

    Raises:
        HTTPException: If email or username is already in use.
    """
    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with such email already exists",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with such username aleady exists",
        )
    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )
    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Authenticate a user and issue access and refresh tokens.

    Args:
        form_data (OAuth2PasswordRequestForm): User credentials from form.
        db (Session): SQLAlchemy session for database interaction.

    Returns:
        Token: Access and refresh tokens for the authenticated user.

    Raises:
        HTTPException: If credentials are invalid or email is unverified.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email is not verified",
        )
    access_token = await create_access_token(data={"sub": user.username})
    refresh_token = await create_refresh_token(data={"sub": user.username})
    user.refresh_token = refresh_token
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Confirm a user's email address using a verification token.

    Args:
        token (str): Email confirmation token.
        db (Session): SQLAlchemy session for database interaction.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: If the token is invalid or user does not exist.
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already verified"}
    await user_service.confirmed_email(email)
    return {"message": "Email is verified successfully"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Send a new email verification link.

    Args:
        body (RequestEmail): Email address of the user.
        background_tasks (BackgroundTasks): Background task handler.
        request (Request): HTTP request for base URL.
        db (Session): SQLAlchemy session for database interaction.

    Returns:
        dict: Message indicating result.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user.confirmed:
        return {"message": "Your email is already verified"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Check your email for verification"}


@router.post("/refresh-token", response_model=Token)
async def new_token(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    """
    Generate a new access token using a refresh token.

    Args:
        request (TokenRefreshRequest): Request containing the refresh token.
        db (Session): SQLAlchemy session for database interaction.

    Returns:
        Token: New access token and the same refresh token.

    Raises:
        HTTPException: If the refresh token is invalid or expired.
    """
    user = await verify_refresh_token(request.refresh_token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    new_access_token = await create_access_token(data={"sub": user.username})
    return {
        "access_token": new_access_token,
        "refresh_token": request.refresh_token,
        "token_type": "bearer",
    }


@router.post("/password-reset-request")
async def reset_password_request(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Initiate a password reset process by sending a reset link via email.

    Args:
        body (RequestEmail): User's email address.
        background_tasks (BackgroundTasks): Background task handler.
        request (Request): HTTP request for base URL.
        db (Session): SQLAlchemy session for database interaction.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: If the user is not found.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    token = await generate_reset_token(user.email)
    background_tasks.add_task(
        send_password_reset_email, user.email, token, request.base_url
    )
    return {"message": "Reset link sent"}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset a user's password using a valid reset token.

    Args:
        body (ResetPasswordRequest): Contains the reset token and new password.
        db (Session): SQLAlchemy session for database interaction.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: If the token is invalid or the user does not exist.
    """
    try:
        payload = jwt.decode(
            body.token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("scope") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token scope"
            )

        email = payload.get("email")
    except JWTError as e:
        raise e

    user_service = UserService(db)
    user = user_service.get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    new_password = Hash().get_password_hash(body.new_password)
    await user_service.reset_password(email, new_password)
    return {"message": "Password was reset"}
