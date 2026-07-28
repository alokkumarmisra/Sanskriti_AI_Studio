"""Test database connection and project count."""
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM projects"))
    print(f"Projects in DB: {result.scalar()}")
    
    result = conn.execute(text("SELECT id, name, status FROM projects ORDER BY id"))
    rows = result.fetchall()
    for row in rows:
        print(f"  - {row.name} (status: {row.status}, id: {row.id})")