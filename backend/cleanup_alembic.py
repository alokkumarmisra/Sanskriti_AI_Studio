# Script to clean up stale Alembic version entries from database

from sqlalchemy import create_engine, text


def cleanup():
    """Remove stale alembic_version entries."""
    
    # Connect to PostgreSQL and create the database if needed
    print("Connecting to PostgreSQL...")
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/postgres')
    
    with engine.connect() as conn:
        # Create database if it doesn't exist
        try:
            conn.execute(text('CREATE DATABASE sanskriti_ai_studio'))
            print("Created database: sanskriti_ai_studio")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("Database already exists")
            else:
                print(f"Warning: {e}")
    
    # Now connect to the new database and clean up
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/sanskriti_ai_studio')
    
    with engine.connect() as conn:
        # Drop the problematic entry if it exists
        result = conn.execute(text("DELETE FROM alembic_version WHERE version = '8014cb051d70';"))
        print(f"Deleted {result.rowcount} stale revision entries")


if __name__ == "__main__":
    cleanup()