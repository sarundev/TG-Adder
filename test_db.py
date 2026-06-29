import os
from dotenv import load_dotenv
from sqlalchemy import text
from database import engine

# Load environment variables from .env
load_dotenv()

def test_connection():
    if not engine:
        print("❌ No database connection configured. Please check your .env file.")
        return

    try:
        # Try to connect and execute a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Successfully connected to the PostgreSQL database!")
            print(f"Connection URL used (hidden password): postgresql://{os.getenv('DB_USER')}:***@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")
    except Exception as e:
        print("❌ Failed to connect to the database. Error details:")
        print(str(e))

if __name__ == "__main__":
    test_connection()
