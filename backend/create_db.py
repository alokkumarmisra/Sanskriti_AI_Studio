# Script to create the database for Alembic migrations

import subprocess


def create_db():
    """Create the database for Alembic migrations."""
    
    # Create a Python script inline
    python_script = '''
from sqlalchemy import create_engine, text

# Connect to PostgreSQL
engine = create_engine('postgresql://postgres:postgres@localhost:5432/postgres')

with engine.connect() as conn:
    conn.execute(text('CREATE DATABASE sanskriti_ai_studio'))

print("Database created successfully")
'''
    
    # Execute the Python script
    result = subprocess.run(['uv', 'run', 'python', '-'], input=python_script, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)


if __name__ == '__main__':
    create_db()