from pydantic import BaseModel

class OTPRequest(BaseModel):
    mobile: str

class OTPVerify(BaseModel):
    mobile: str
    otp: str

class Message(BaseModel):
    sender: str
    receiver: str
    text: str

class WSMessage(BaseModel):
    sender: str
    receiver: str
    text: str
