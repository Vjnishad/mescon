import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Import all your routers
from auth import router as auth_router
from chat import router as chat_router
from user_management import router as users_router
from profile import router as profile_router # <-- THIS LINE IS ADDED

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = FastAPI(
    title="Chatters App Backend",
    description="Backend API with OTP login & WebSocket chat",
    version="1.0.0"
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routes ---
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(users_router, prefix="/api", tags=["Users"])
app.include_router(profile_router, prefix="/api", tags=["Profile"]) # <-- THIS LINE IS ADDED

# --- Static Files Mount ---
# This serves your frontend files from the "static" folder.
# It must be placed AFTER all your API routes.
app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True), name="static")

# --- Uvicorn Runner ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

