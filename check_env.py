import os
from dotenv import load_dotenv

print("--- Starting Environment Check ---")

# This line tells the script where to look for the .env file
# It looks in the same directory where the script is run.
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Looking for .env file at: {dotenv_path}")

# Load the .env file
load_dotenv(dotenv_path=dotenv_path)

# Get the DATABASE_URL variable
database_url = os.getenv("DATABASE_URL")

# Print the result
if database_url:
    print("\n✅ SUCCESS! The .env file was loaded correctly.")
    print(f"The DATABASE_URL is: {database_url}")
else:
    print("\n❌ FAILED! The .env file was NOT loaded correctly.")
    print("The DATABASE_URL is empty (None).")
    print("\nPlease double-check that:")
    print("1. The .env file is in the same folder as this script.")
    print("2. The file is named exactly '.env' (and not '.env.txt').")
    print("3. The file contains the line: DATABASE_URL=your_connection_string")

print("\n--- Environment Check Finished ---")