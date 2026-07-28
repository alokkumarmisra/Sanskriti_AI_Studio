#!/usr/bin/env python3
"""Check Alembic database state."""

from sqlalchemy import create_engine, text


def check():
    """Check the alembic_version table state."""
    
    print("Connecting to PostgreSQL...")
    
    # Connect to the target database
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/sanskriti_ai_studio')
    
    with engine.connect() as conn:
        # Check current version in alembic_version table
        result = conn.execute(text("SELECT * FROM alembic_version;"))
        rows = result.fetchall()
        
        if rows:
            print(f"Current alembic_version entries:")
            for row in rows:
                print(f"  - {row}")
        else:
            print("alembic_version table is empty (good!)")


if __name__ == "__main__":
    check()