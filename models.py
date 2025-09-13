from sqlalchemy import create_engine, Column, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

# This line reads the secrets from your .env file
load_dotenv()

# This correctly gets the value of the variable named "DATABASE_URL" from your .env file.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("FATAL ERROR: DATABASE_URL not found in .env file. Please check your setup.")

Base = declarative_base()

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

# This uses a standard (non-async) engine, which is correct for table creation
engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)