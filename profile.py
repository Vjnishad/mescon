import json
import os
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict

# Import the dependency to get the current user
from dependencies import get_current_user_http

# --- Configuration ---
USERS_FILE = "users.json"  # We'll store profile info in the main users file


# --- Pydantic Model for Profile Updates ---
class ProfileUpdateRequest(BaseModel):
    name: str
    avatar: str


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


def save_all_users(users: Dict[str, Dict]):
    """Saves the master list of all registered users."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


# --- Router Definition ---
router = APIRouter()


@router.get("/profile")
async def get_my_profile(current_user: str = Depends(get_current_user_http)):
    """Fetches the profile information for the currently logged-in user."""
    users = load_all_users()
    if current_user not in users:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return users[current_user]


@router.put("/profile")
async def update_my_profile(request: ProfileUpdateRequest, current_user: str = Depends(get_current_user_http)):
    """Updates the name and avatar for the currently logged-in user."""
    users = load_all_users()
    if current_user not in users:
        raise HTTPException(status_code=404, detail="User profile not found.")

    # Update the user's data
    users[current_user]["name"] = request.name
    users[current_user]["avatar"] = request.avatar

    save_all_users(users)

    return {"message": "Profile updated successfully.", "profile": users[current_user]}