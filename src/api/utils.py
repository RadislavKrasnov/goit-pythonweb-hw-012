from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.database.db import get_db

router = APIRouter(tags=["utils"])


@router.get("/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint to verify database connectivity.

    This endpoint runs a simple SQL query (`SELECT 1`) against the database
    to confirm that the database connection is properly configured and accessible.

    Args:
        db (AsyncSession, optional): Asynchronous database session injected via FastAPI dependency.

    Returns:
        dict: A JSON response with a welcome message if the database is reachable.

    Raises:
        HTTPException: Raises a 500 Internal Server Error if the database query fails
                       or the database is not configured correctly.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.scalar_one_or_none()

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database is not configured correctly",
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the database",
        )
