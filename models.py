# models.py - Updated for Asynchronous SQLAlchemy

from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
# 🛑 NEW IMPORTS for Async Engine and functionality
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncEngine 

import os
from dotenv import load_dotenv

# This line reads the secrets from your .env file
load_dotenv()

# This correctly gets the value of the variable named "DATABASE_URL" from your .env file.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("FATAL ERROR: DATABASE_URL not found in .env file. Please check your setup.")

Base = declarative_base()

# ----------------- Model Definitions Remain the Same -----------------

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True) # Phone number
    name = Column(String)
    avatar = Column(String)

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(String, primary_key=True, default=lambda: os.urandom(16).hex())
    user_id = Column(String, ForeignKey("users.id"))
    contact_user_id = Column(String, ForeignKey("users.id"))
    custom_name = Column(String)

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: os.urandom(16).hex())
    sender_id = Column(String, ForeignKey("users.id"))
    recipient_id = Column(String, ForeignKey("users.id"))
    text = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# ----------------- Asynchronous Engine Setup -----------------

# 🛑 FIX 1: Use create_async_engine (imported above)
# This also ensures the URL uses the '+asyncpg' dialect and forces SSL for platforms like Render.
async_engine: AsyncEngine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    # 🛑 FIX 2: Use the 'ssl' argument, which asyncpg accepts.
    connect_args={
        "ssl": "require"
    }
)

# ----------------- Asynchronous Table Creation -----------------

# 🛑 FIX 3: This function must be async
async def create_db_and_tables():
    """Creates all database tables using the asynchronous engine."""
    
    # Use the async engine's context manager
    async with async_engine.begin() as conn:
        # Use run_sync() to wrap the synchronous metadata creation command.
        # This is the correct pattern for running synchronous operations (like DDL) 
        # on an asynchronous engine.
        await conn.run_sync(Base.metadata.create_all)

# Note: You should now use 'async_engine' in your database.py file as well. 
# Make sure your main.py calls 'await create_db_and_tables()' in the startup event.
