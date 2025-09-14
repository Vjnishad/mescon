import json
from datetime import datetime
import pytz
from fastapi import APIRouter, WebSocket, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Dict

from dependencies import get_user_from_token, get_current_user_http
from database import get_db_session
from models import Message

# Set the timezone to India Standard Time
IST = pytz.timezone('Asia/Kolkata')

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User '{user_id}' connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User '{user_id}' disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()

def get_current_user_ws(token: str = Query(...)):
    return get_user_from_token(token)

@router.get("/history")
async def get_chat_history(
    current_user: str = Depends(get_current_user_http),
    session: AsyncSession = Depends(get_db_session)
):
    query = (
        select(Message)
        .where(or_(Message.sender_id == current_user, Message.recipient_id == current_user))
        .order_by(Message.timestamp)
    )
    result = await session.execute(query)
    
    user_history = {}
    for msg in result.scalars().all():
        other_user = msg.sender_id if msg.recipient_id == current_user else msg.recipient_id
        if other_user not in user_history:
            user_history[other_user] = []
        
        user_history[other_user].append({
            "text": msg.text,
            "sender": "me" if msg.sender_id == current_user else "them",
            "timestamp": msg.timestamp.isoformat()
        })
    return user_history


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Depends(get_current_user_ws),
    session: AsyncSession = Depends(get_db_session)
):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "chat_message":
                recipient_id = data.get("recipient_id")
                text = data.get("text")
                if recipient_id and text:
                    timestamp_now = datetime.now(IST)
                    
                    new_message = Message(
                        sender_id=user_id,
                        recipient_id=recipient_id,
                        text=text,
                        timestamp=timestamp_now
                    )
                    session.add(new_message)
                    await session.commit()
                    
                    message_to_send = {
                        "type": "chat_message",
                        "sender_id": user_id,
                        "recipient_id": recipient_id, # Include recipient for frontend logic
                        "text": text,
                        "timestamp": timestamp_now.isoformat()
                    }
                    # Send to the other person
                    await manager.send_personal_message(json.dumps(message_to_send), str(recipient_id))
                    # --- THIS IS THE FIX ---
                    # Send a confirmation copy back to the person who sent it.
                    await manager.send_personal_message(json.dumps(message_to_send), str(user_id))
                    
            elif msg_type in ["webrtc_offer", "webrtc_answer", "webrtc_ice_candidate", "call_ended", "call_declined"]:
                recipient_id = data.get("recipient_id")
                data["sender_id"] = user_id
                await manager.send_personal_message(json.dumps(data), str(recipient_id))

    except Exception as e:
        print(f"Connection closed for user '{user_id}': {e}")
    finally:
        manager.disconnect(user_id)
