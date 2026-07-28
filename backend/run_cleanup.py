#!/usr/bin/env python3
"""Script to reset Alembic database state for clean migrations."""

from sqlalchemy import create_engine, text


def cleanup():
    """Clear alembic_version table and reset migration state."""
    
    print("Resetting Alembic database state...")
    
    engine = create_engine(
        'postgresql://postgres:postgres@localhost:5432/sanskriti_ai_studio',
        isolation_level='AUTOCOMMIT',
        pool_size=0,
        max_overflow=0
    )
    
    with engine.begin() as conn:
        # Drop the table entirely
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        print("Dropped alembic_version table")
        
        # Create fresh table with exact schema Alembic expects (version_num column)
        conn.execute(text("""
            CREATE TABLE alembic_version (
                version_num INTEGER NOT NULL,
                PRIMARY KEY (version_num)
            )
        """))
        print("Created fresh alembic_version table with 'version_num' column")
        
        # Grant permissions to postgres user so Alembic can write to it
        conn.execute(text("GRANT ALL PRIVILEGES ON TABLE alembic_version TO postgres"))
        print("Granted permissions to postgres user")
    
    print("\nSUCCESS: Alembic database is ready for migrations!")


if __name__ == "__main__":
    cleanup()