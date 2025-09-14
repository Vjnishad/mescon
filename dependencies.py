import jwt
from fastapi import Header, HTTPException, status
from typing import Dict

# --- Configuration (Must be consistent across all files) ---
SECRET_KEY = "your-super-secret-key-that-is-long-and-secure"
ALGORITHM = "HS256"

# --- Centralized Dependency to get user from Token ---
# Both chat.py and user_management.py will use this function.

def get_user_from_token(token: str):
    """Decodes the JWT token to get the user's ID (phone number)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

def get_current_user_http(authorization: str = Header(...)):
    """Dependency for regular HTTP endpoints that reads the token from the header."""
    try:
        token = authorization.split(" ")[1] # Expects "Bearer TOKEN"
        return get_user_from_token(token)
    except IndexError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token not found")