import jwt
import random
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

# --- THIS IS THE FIX ---
# Import the function from the renamed user_management.py file
from user_management import add_user_if_not_exists

# --- Configuration ---
SECRET_KEY = "your-super-secret-key-that-is-long-and-secure"
ALGORITHM = "HS256"

# --- In-memory OTP Storage ---
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
async def verify_otp(request: OTPVerifyRequest):
    stored_otp = otp_storage.get(request.mobile)

    if not stored_otp:
        raise HTTPException(
            status_code=400, detail="OTP not requested or has expired."
        )

    if request.otp == stored_otp:
        del otp_storage[request.mobile]

        # This now correctly calls the function from the renamed file
        add_user_if_not_exists(request.mobile)

        access_token = create_access_token(data={"sub": request.mobile})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")
