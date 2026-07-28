# Script to create the database for Alembic migrations (standalone)

import subprocess


def create_db():
    """Create the database for Alembic migrations using psql."""
    
    # Connect to postgres and create the database
    try:
        result = subprocess.run([
            "psql", "-U", "postgres", 
            "-d", "postgres",  # Connect to postgres database first
            "-c", "CREATE DATABASE sanskriti_ai_studio;"
        ], check=False)
        
        if result.returncode == 0:
            print("Database created successfully: sanskriti_ai_studio")
        else:
            print("Could not create database (it may already exist)")
    except Exception as e:
        print(f"Error creating database: {e}")


if __name__ == '__main__':
    create_db()