import json
import os
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict
import jwt

# --- Configuration (Must be consistent) ---
SECRET_KEY = "your-super-secret-key-that-is-long-and-secure"
ALGORITHM = "HS256"
USERS_FILE = "users.json"
CONTACTS_DIR = "user_contacts"

# Create the contacts directory if it doesn't exist
os.makedirs(CONTACTS_DIR, exist_ok=True)


# --- Pydantic Model for Adding/Updating a Contact ---
class ContactRequest(BaseModel):
    number: str
    name: str


# --- Dependency to get user from HTTP Header Token ---
def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def get_current_user_http(authorization: str = Header(...)):
    token = authorization.split(" ")[1]  # "Bearer TOKEN"
    return get_user_from_token(token)


# --- User Database Functions ---

def load_all_users() -> Dict[str, Dict]:
    """Loads the master list of all registered users."""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def add_user_if_not_exists(user_id: str):
    """Adds a new user to the master database if they aren't already there."""
    users = load_all_users()
    if user_id not in users:
        users[user_id] = {
            "id": user_id,
            "name": f"User {user_id[-4:]}",
            "avatar": f"https://placehold.co/40x40/1e88e5/ffffff?text={user_id[-2:]}",
            "online": True
        }
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)
        print(f"New user '{user_id}' registered in master list.")


# --- Personal Contact List Functions ---

def get_user_contacts_path(user_id: str) -> str:
    """Returns the file path for a user's personal contact list."""
    return os.path.join(CONTACTS_DIR, f"{user_id}.json")


def load_user_contacts(user_id: str) -> Dict[str, str]:
    """Loads a specific user's personal contact list."""
    path = get_user_contacts_path(user_id)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_user_contacts(user_id: str, contacts: Dict[str, str]):
    """Saves a user's personal contact list to their file."""
    path = get_user_contacts_path(user_id)
    with open(path, "w") as f:
        json.dump(contacts, f, indent=4)


# --- Router Definition ---
router = APIRouter()


@router.get("/users")
async def get_my_contacts(current_user: str = Depends(get_current_user_http)):
    """
    Fetches the personalized contact list for the currently logged-in user.
    """
    all_users = load_all_users()
    my_contact_numbers = load_user_contacts(current_user)

    contact_list = []
    for number, custom_name in my_contact_numbers.items():
        if number in all_users:
            contact_info = all_users[number].copy()
            contact_info["name"] = custom_name
            contact_list.append(contact_info)

    return contact_list


@router.post("/contacts")
async def add_contact(request: ContactRequest, current_user: str = Depends(get_current_user_http)):
    """
    Adds a new contact to the current user's personal list.
    """
    all_users = load_all_users()
    if request.number not in all_users:
        raise HTTPException(status_code=404, detail="User with this number is not registered in the app.")

    my_contacts = load_user_contacts(current_user)
    my_contacts[request.number] = request.name
    save_user_contacts(current_user, my_contacts)

    return {"message": f"Contact '{request.name}' added successfully."}


# --- THIS IS THE NEW UPDATE ENDPOINT ---
@router.put("/contacts/{contact_number}")
async def update_contact(contact_number: str, request: ContactRequest,
                         current_user: str = Depends(get_current_user_http)):
    """
    Updates the name of an existing contact in the user's personal list.
    """
    my_contacts = load_user_contacts(current_user)
    if contact_number not in my_contacts:
        raise HTTPException(status_code=404, detail="Contact not found in your list.")

    my_contacts[contact_number] = request.name
    save_user_contacts(current_user, my_contacts)
    return {"message": f"Contact updated to '{request.name}'."}


# --- THIS IS THE NEW DELETE ENDPOINT ---
@router.delete("/contacts/{contact_number}")
async def delete_contact(contact_number: str, current_user: str = Depends(get_current_user_http)):
    """
    Deletes a contact from the user's personal list.
    """
    my_contacts = load_user_contacts(current_user)
    if contact_number not in my_contacts:
        raise HTTPException(status_code=404, detail="Contact not found in your list.")

    del my_contacts[contact_number]
    save_user_contacts(current_user, my_contacts)
    return {"message": "Contact deleted successfully."}


