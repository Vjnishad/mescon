import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Show current working directory
print(f"📂 Current working directory: {os.getcwd()}")

# Force-load the .env file from the same directory as database.py
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"🔍 Trying to load .env from: {env_path}")

load_dotenv(dotenv_path=env_path)

# Check values
print(f"📜 MONGO_URI from .env: {os.getenv('MONGO_URI')}")
print(f"📜 DB_NAME from .env: {os.getenv('DB_NAME')}")

# Now assign
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in .env file")
if not DB_NAME:
    raise ValueError("DB_NAME is not set in .env file")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

print(f"✅ Connected to database: {DB_NAME}")

def get_collection(name: str):
    return db[name]
