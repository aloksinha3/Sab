#!/usr/bin/env python3
"""Initialize the database for SabCare"""

from database import Database
import os

def main():
    db_path = os.getenv("DB_PATH", "patients.db")
    db = Database(db_path)
    print(f"✅ Database initialized at {db_path}")
    print("✅ Tables created: patients, patient_messages, call_logs")

if __name__ == "__main__":
    main()

