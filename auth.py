import jwt
import random
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession

# Import the function to add a new user and the database dependency
from user_management import add_user_if_not_exists
from database import get_db_session

# --- Configuration ---
SECRET_KEY = "your-super-secret-key-that-is-long-and-secure"
ALGORITHM = "HS256"

# In-memory OTP Storage (remains the same)
otp_storage: Dict[str, str] = {}


# --- Pydantic Models ---
class OTPSendRequest(BaseModel):
    mobile: str


class OTPVerifyRequest(BaseModel):
    mobile: str
    otp: str


# --- JWT Token Creation ---
def create_access_token(data: dict):
    to_encode = data.copy()
    # No expiration for simplicity in this prototype
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- Router Definition ---
router = APIRouter()


@router.post("/send-otp")
async def send_otp(request: OTPSendRequest):
    otp = str(random.randint(100000, 999999))
    otp_storage[request.mobile] = otp
    print(f"OTP for {request.mobile}: {otp}")
    return {"message": "OTP sent successfully"}


@router.post("/verify-otp")
async def verify_otp(
    request: OTPVerifyRequest,
    session: AsyncSession = Depends(get_db_session) # Get a database session
):
    stored_otp = otp_storage.get(request.mobile)

    if not stored_otp or request.otp != stored_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # If OTP is correct, clear it from storage
    if request.mobile in otp_storage:
        del otp_storage[request.mobile]

    # --- THIS IS THE KEY UPDATE ---
    # After successful verification, add the user to our database.
    # We pass the database session to this function.
    await add_user_if_not_exists(request.mobile, session)

    access_token = create_access_token(data={"sub": request.mobile})
    return {"access_token": access_token, "token_type": "bearer"}