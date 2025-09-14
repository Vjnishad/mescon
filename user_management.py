from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from pydantic import BaseModel

from dependencies import get_current_user_http
from database import get_db_session
from models import User, Contact

router = APIRouter()


class ContactAddRequest(BaseModel):
    number: str
    name: str


async def add_user_if_not_exists(user_id: str, session: AsyncSession):
    # Check if the user already exists in the database
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    # If the user does not exist, create a new one
    if not user:
        new_user = User(
            id=user_id,
            name=f"User {user_id[-4:]}",  # e.g., "User 9748"
            avatar=f"https://placehold.co/40x40/1e88e5/ffffff?text={user_id[-2:]}"
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)  # Refresh to get the new object state
        print(f"New user '{user_id}' registered in the database.")


@router.get("/users")
async def get_my_contacts(
        current_user: str = Depends(get_current_user_http),
        session: AsyncSession = Depends(get_db_session)
):
    # --- THIS IS THE FIX ---
    # The original query had a subtle issue. This is the correct, robust way to join
    # the tables and retrieve the contact's information along with the custom name.
    query = (
        select(
            Contact.contact_user_id.label("id"),
            Contact.custom_name.label("name"),
            User.avatar.label("avatar")
        )
        .join(User, Contact.contact_user_id == User.id)
        .where(Contact.user_id == current_user)
    )
    result = await session.execute(query)
    contacts = [
        {"id": r.id, "name": r.name, "avatar": r.avatar, "online": True}  # online status is a placeholder
        for r in result.mappings().all()
    ]
    return contacts


@router.post("/contacts")
async def add_contact(
        request: ContactAddRequest,
        current_user: str = Depends(get_current_user_http),
        session: AsyncSession = Depends(get_db_session)
):
    # Check if the user you are trying to add exists in the master user list
    result = await session.execute(select(User).where(User.id == request.number))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User with this number is not registered in the app.")

    # Check if contact already exists in your personal list
    existing_contact_query = select(Contact).where(
        Contact.user_id == current_user,
        Contact.contact_user_id == request.number
    )
    result = await session.execute(existing_contact_query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Contact already exists.")

    # Create the new contact
    new_contact = Contact(
        user_id=current_user,
        contact_user_id=request.number,
        custom_name=request.name
    )
    session.add(new_contact)
    await session.commit()
    return {"message": f"Contact '{request.name}' added successfully."}


@router.put("/contacts/{contact_id}")
async def update_contact(
        contact_id: str,
        request: ContactAddRequest,
        current_user: str = Depends(get_current_user_http),
        session: AsyncSession = Depends(get_db_session)
):
    query = (
        update(Contact)
        .where(Contact.user_id == current_user, Contact.contact_user_id == contact_id)
        .values(custom_name=request.name)
    )
    await session.execute(query)
    await session.commit()
    return {"message": "Contact updated successfully."}


@router.delete("/contacts/{contact_id}")
async def delete_contact(
        contact_id: str,
        current_user: str = Depends(get_current_user_http),
        session: AsyncSession = Depends(get_db_session)
):
    query = delete(Contact).where(Contact.user_id == current_user, Contact.contact_user_id == contact_id)
    await session.execute(query)
    await session.commit()
    return {"message": "Contact deleted successfully."}