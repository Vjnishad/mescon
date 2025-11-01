import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Import your routers and database setup
from auth import router as auth_router
from chat import router as chat_router
from user_management import router as users_router
from profile import router as profile_router
from models import create_db_and_tables

# ---------- Server Lifecycle ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Server Starting Up...")
    create_db_and_tables()
    print("✅ Database Tables Verified")
    yield
    print("🛑 Server Shutting Down...")

# ---------- Load Environment ----------
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- Initialize App ----------
app = FastAPI(
    lifespan=lifespan,
    title="MESCON Backend",
    description="Backend for MESCON App (FastAPI + PostgreSQL + OTP + WebSocket)",
    version="2.0.0"
)

# ---------- CORS ----------
# Allow both app and browser frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can later restrict this to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Routers ----------
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(users_router, prefix="/api", tags=["Users"])
app.include_router(profile_router, prefix="/api", tags=["Profile"])

# ---------- Serve Frontend ----------
# The frontend (HTML, JS, CSS) is in ./static folder
frontend_path = os.path.join(BASE_DIR, "static")

if not os.path.exists(frontend_path):
    os.makedirs(frontend_path)  # Make sure directory exists

app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

# ---------- Run Server ----------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
