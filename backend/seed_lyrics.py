"""Seed script to populate lyrics table with sample data."""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from uuid import uuid4

def seed_lyrics():
    """Insert sample lyrics into the database."""
    
    engine = create_engine("postgresql://postgres:postgres@localhost/sanskriti_db")
    
    with engine.connect() as conn:
        # Get existing projects
        result = conn.execute(text("""
            SELECT id, name FROM projects 
            ORDER BY name LIMIT 1
        """))
        rows = result.fetchall()
        
        if not rows:
            print("No projects found. Creating a sample project first...")
            conn.execute(text("""
                INSERT INTO projects (id, name, description, project_type, status, slug, created_at, updated_at)
                VALUES (:id, :name, :description, :project_type, :status, :slug, NOW(), NOW())
            """), {
                "id": str(uuid4()),
                "name": "Sample Project",
                "description": "A sample project for development",
                "project_type": "general",
                "status": "active",
                "slug": "sample-project"
            })
            conn.commit()
        
        # Get the first project ID
        row = rows[0] if rows else None
        project_id = str(row.id) if row else None
        
        # Sample lyrics to insert
        sample_lyrics = [
            {
                "project_id": project_id,
                "title": "Morning Prayer",
                "content": "Rise up early, praise the divine,\nFill your heart with grace and sign.\nThe morning light will guide your way,\nBlessings all throughout the day.",
                "language": "English",
                "status": "draft"
            },
            {
                "project_id": project_id,
                "title": "Evening Reflections",
                "content": "As sun sets low and shadows grow,\nReflect on all you know below.\nGratitude for gifts received,\nPeace of mind is now achieved.",
                "language": "English",
                "status": "draft"
            },
            {
                "project_id": project_id,
                "title": "Devotional Chorus",
                "content": "O divine, you guide us all,\nThrough valleys deep and over walls.\nYour love is strong, your light is true,\nShow me how to walk in you.",
                "language": "Hindi",
                "status": "ready"
            },
            {
                "project_id": project_id,
                "title": "Peaceful Journey",
                "content": "Walk gently on this sacred ground,\nLet love be your only sound.\nThe path ahead is clear to see,\nWith faith as our companions free.",
                "language": "English",
                "status": "ready"
            },
        ]
        
        # Insert lyrics
        for lyrics in sample_lyrics:
            if project_id:  # Only insert if we have a project
                conn.execute(text("""
                    INSERT INTO lyrics (id, project_id, title, content, language, status, created_at, updated_at)
                    VALUES (:id, :project_id, :title, :content, :language, :status, NOW(), NOW())
                """), {
                    "id": str(uuid4()),
                    **lyrics
                })
        
        conn.commit()
        print("Sample lyrics seeded successfully!")
        print(f"Project ID: {project_id}")

if __name__ == "__main__":
    seed_lyrics()