import json
import os
from database import engine, db_save_licenses, db_save_web_users

def migrate():
    print("Starting migration from JSON to PostgreSQL...")
    if not engine:
        print("Database not configured. Migration aborted.")
        return

    # Migrate licenses
    if os.path.exists("accounts/licenses.json"):
        with open("accounts/licenses.json", "r") as f:
            licenses_data = json.load(f)
        db_save_licenses(licenses_data)
        print(f"Migrated {len(licenses_data)} licenses to DB.")

    # Migrate web users
    if os.path.exists("accounts/web_users.json"):
        with open("accounts/web_users.json", "r") as f:
            users_data = json.load(f)
        db_save_web_users(users_data)
        print(f"Migrated {len(users_data)} web users to DB.")
        
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
