from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# This line reads the secrets from your .env file
load_dotenv()

# This correctly gets the value of the variable named "DATABASE_URL" from your .env file.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("FATAL ERROR: DATABASE_URL not found in .env file. Please check your setup.")

# Make sure to use the async version of the driver
async_engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))

# Create a configured "AsyncSession" class
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Dependency to get a database session
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session