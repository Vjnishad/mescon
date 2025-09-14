import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from auth import router as auth_router
from chat import router as chat_router
from user_management import router as users_router
from profile import router as profile_router
from models import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Server Starting Up ---")
    create_db_and_tables()
    print("--- Database Tables Verified ---")
    yield
    print("--- Server Shutting Down ---")

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = FastAPI(
    lifespan=lifespan,
    title="Mescon App Backend",
    description="Backend with PostgreSQL, OTP login & WebSocket chat",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mescon.onrender.com"],  # Specify your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(users_router, prefix="/api", tags=["Users"])
app.include_router(profile_router, prefix="/api", tags=["Profile"])

app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port
    )
