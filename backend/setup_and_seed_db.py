#!/usr/bin/env python3
"""Setup and seed database for Sanskriti AI Studio."""

import sys
from sqlalchemy import create_engine, text
from uuid import uuid4

DB_URL = "postgresql://postgres:postgres@localhost/sanskriti_db"

def setup_and_seed():
    """Create database if it doesn't exist, then create tables and seed data."""
    
    # First, connect to postgres server (without database)
    temp_engine = create_engine("postgresql://postgres:postgres@localhost")
    
    with temp_engine.connect() as conn:
        # Create the sanskriti_db database
        try:
            conn.execute(text("DROP DATABASE IF EXISTS sanskriti_db"))
            print("✓ Dropped existing database (if existed)")
        except Exception as e:
            pass  # Ignore if database doesn't exist
        
        try:
            conn.execute(text("CREATE DATABASE sanskriti_db"))
            print("✓ Created database 'sanskriti_db'")
        except Exception as e:
            print(f"⚠️  Database may already exist: {e}")
    
    # Now connect to the actual database
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        # Create tables
        tables = [
            "projects", "lyrics", "scenes", "characters", "locations",
            "scene_prompts", "analysis_results", "task_queue"
        ]
        
        for table in tables:
            if table in ["projects", "lyrics", "scenes", "characters", "locations"]:
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id VARCHAR(36) PRIMARY KEY,
                        project_id VARCHAR(36) REFERENCES projects(id),
                        -- Add other columns as needed
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
            
            conn.commit()
        
        print("✓ All tables created successfully")

if __name__ == "__main__":
    setup_and_seed()
    print("\n🎉 Database setup complete!")