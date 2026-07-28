"""Fix project table schema by adding missing columns."""

from sqlalchemy import create_engine, text
from app.core.settings import Settings


def main():
    s = Settings()
    engine = create_engine(
        f'postgresql://postgres:postgres@localhost:{s.DB_PORT}/{s.DB_NAME}',
        echo=True
    )
    
    conn = engine.connect()
    
    # Add project_type column with default value 'general'
    conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_type VARCHAR(64) DEFAULT 'general'"))
    
    # Add status column with default value 'draft'
    conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'draft'"))
    
    conn.commit()
    print("Columns added successfully to projects table")


if __name__ == '__main__':
    main()