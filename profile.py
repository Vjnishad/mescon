from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from dependencies import get_current_user_http
from database import get_db_session
from models import User

router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    name: str
    avatar: str


@router.get("/profile")
async def get_my_profile(
        current_user: str = Depends(get_current_user_http),
        session: AsyncSession = Depends(get_db_session)
):
    """Fetches the profile information for the currently logged-in user."""
    result = await session.execute(select(User).where(User.id == current_user))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return user


@router.put("/profile")
async def update_my_profile(
        request: ProfileUpdateRequest,
        current_user: str = Depends(get_current_user_http),
        session: AsyncSession = Depends(get_db_session)
):
    """Updates the name and avatar for the currently logged-in user."""
    query = (
        update(User)
        .where(User.id == current_user)
        .values(name=request.name, avatar=request.avatar)
    )
    await session.execute(query)
    await session.commit()

    # Fetch the updated profile to return it
    result = await session.execute(select(User).where(User.id == current_user))
    updated_user = result.scalar_one_or_none()

    return {"message": "Profile updated successfully.", "profile": updated_user}