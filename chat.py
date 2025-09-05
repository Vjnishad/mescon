import jwt
import json
import os
import datetime
from fastapi import APIRouter, WebSocket, Depends, Query, HTTPException, status, Header
from typing import Dict, List
import pytz  # Import the pytz library for timezone handling

# Import the dependency from our central file
from dependencies import get_user_from_token, get_current_user_http

# --- Configuration ---
MESSAGES_FILE = "messages.json"
# --- THIS IS THE FIX: Define your local timezone ---
IST = pytz.timezone('Asia/Kolkata')


# --- Helper Functions for Database (JSON file) ---

def load_messages() -> Dict[str, List[Dict]]:
    """Loads all messages from the JSON file."""
    if not os.path.exists(MESSAGES_FILE):
        return {}
    with open(MESSAGES_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_message(sender_id: str, recipient_id: str, text: str, timestamp: str):
    """Saves a single message to the JSON file with a timestamp."""
    all_messages = load_messages()
    convo_key = "-".join(sorted([sender_id, recipient_id]))

    if convo_key not in all_messages:
        all_messages[convo_key] = []

    new_message = {"sender": sender_id, "text": text, "timestamp": timestamp}
    all_messages[convo_key].append(new_message)

    with open(MESSAGES_FILE, "w") as f:
        json.dump(all_messages, f, indent=4)


# --- WebSocket Connection Manager ---
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


# WebSocket dependency
def get_current_user_ws(token: str = Query(...)):
    return get_user_from_token(token)


# --- Router Definition ---
router = APIRouter()


@router.get("/history")
async def get_chat_history(current_user: str = Depends(get_current_user_http)):
    """
    HTTP endpoint to fetch all conversations involving the current user.
    """
    all_messages = load_messages()
    user_history = {}
    for convo_key, messages in all_messages.items():
        participants = convo_key.split("-")
        if current_user in participants:
            other_user = participants[0] if participants[1] == current_user else participants[1]
            user_history[other_user] = []
            for msg in messages:
                sender_type = "me" if msg["sender"] == current_user else "them"
                user_history[other_user].append({
                    "sender": sender_type,
                    "text": msg["text"],
                    "timestamp": msg.get("timestamp")
                })
    return user_history


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: str = Depends(get_current_user_ws)):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()

            msg_type = data.get("type")
            recipient_id = data.get("recipient_id")

            if msg_type == "chat_message":
                text = data.get("text")
                if recipient_id and text:
                    # --- THIS IS THE FIX ---
                    # Generate a timestamp using the correct IST timezone
                    timestamp = datetime.datetime.now(IST).isoformat()

                    # Save the message with the correct timestamp
                    save_message(sender_id=user_id, recipient_id=recipient_id, text=text, timestamp=timestamp)

                    # Create the message payload to send to the recipient
                    message_to_send = {
                        "type": "chat_message",
                        "sender_id": user_id,
                        "text": text,
                        "timestamp": timestamp  # Use the server's correct timestamp
                    }
                    await manager.send_personal_message(
                        json.dumps(message_to_send),
                        str(recipient_id)
                    )

                    # Also send the message back to the sender for timestamp consistency
                    await manager.send_personal_message(
                        json.dumps(message_to_send),
                        user_id
                    )

                    print(f"Message from '{user_id}' to '{recipient_id}': {text}")

            elif msg_type in ["webrtc_offer", "webrtc_answer", "webrtc_ice_candidate", "call_ended"]:
                print(f"Relaying '{msg_type}' from '{user_id}' to '{recipient_id}'")
                data["sender_id"] = user_id
                await manager.send_personal_message(json.dumps(data), str(recipient_id))

    except Exception as e:
        print(f"Connection closed for user '{user_id}': {e}")
    finally:
        manager.disconnect(user_id)