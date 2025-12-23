#!/usr/bin/env python3
"""
Admin utility to list all users in the database
Usage: python scripts/list_users.py
"""
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, create_engine, select
from models.database import User

def list_users():
    """List all users in the database"""
    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://brandpulse:brandpulse_dev_password@localhost:5433/brandpulse"
    )

    # Create engine
    engine = create_engine(database_url)

    with Session(engine) as session:
        # Query all users ordered by ID
        users = session.exec(select(User).order_by(User.id)).all()

        # Print header
        print(f"\n{'='*80}")
        print(f"📊 Total Users: {len(users)}")
        print(f"{'='*80}\n")

        # Print each user
        for user in users:
            print(f"ID:       {user.id}")
            print(f"Email:    {user.email}")
            print(f"Username: {user.username}")
            print(f"Active:   {'✓' if user.is_active else '✗'}")
            print(f"Created:  {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'-'*80}")

if __name__ == "__main__":
    try:
        list_users()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
