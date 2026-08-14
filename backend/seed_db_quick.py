# Quick database seeding script - inserts sample data without needing migrations

import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text
from uuid import uuid4
import os

# Database connection string
DB_URL = "postgresql://postgres:postgres@localhost/sanskriti_db"

def seed_database():
    """Create database and insert sample data."""
    
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        # Create projects table if not exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                project_type VARCHAR(100) DEFAULT 'general',
                status VARCHAR(50) DEFAULT 'draft',
                slug VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create lyrics table if not exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lyrics (
                id VARCHAR(36) PRIMARY KEY,
                project_id VARCHAR(36) REFERENCES projects(id),
                title VARCHAR(255),
                content TEXT,
                language VARCHAR(100),
                status VARCHAR(50) DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create scenes table if not exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS scenes (
                id VARCHAR(36) PRIMARY KEY,
                project_id VARCHAR(36) REFERENCES projects(id),
                lyrics_id VARCHAR(36) REFERENCES lyrics(id),
                scene_number INTEGER,
                title VARCHAR(255),
                description TEXT,
                visual_prompt TEXT,
                negative_prompt TEXT,
                duration_seconds INTEGER DEFAULT 8,
                status VARCHAR(50) DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create characters table if not exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS characters (
                id VARCHAR(36) PRIMARY KEY,
                project_id VARCHAR(36) REFERENCES projects(id),
                character_name VARCHAR(255) NOT NULL,
                appearance TEXT,
                role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create locations table if not exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS locations (
                id VARCHAR(36) PRIMARY KEY,
                project_id VARCHAR(36) REFERENCES projects(id),
                location_name VARCHAR(255) NOT NULL,
                description TEXT,
                time_of_day VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.commit()
    
    print("✓ Tables created successfully")
    
    # Now insert sample data
    with engine.connect() as conn:
        # Create a sample project
        result = conn.execute(text("""
            INSERT INTO projects (id, name, description, project_type, status, slug)
            VALUES (:id, :name, :description, :project_type, :status, :slug)
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
        """), {
            "id": str(uuid4()),
            "name": "Demo Project",
            "description": "Sample project for testing",
            "project_type": "general",
            "status": "active",
            "slug": "demo-project"
        })
        print("✓ Created sample project")
        
        # Insert sample lyrics
        sample_lyrics = [
            {
                "title": "Morning Prayer",
                "content": "Rise up early, praise the divine,\nFill your heart with grace and sign.\nThe morning light will guide your way,\nBlessings all throughout the day.",
                "language": "English",
                "status": "draft"
            },
            {
                "title": "Evening Reflections",
                "content": "As sun sets low and shadows grow,\nReflect on all you know below.\nGratitude for gifts received,\nPeace of mind is now achieved.",
                "language": "English",
                "status": "draft"
            },
            {
                "title": "Devotional Chorus",
                "content": "O divine, you guide us all,\nThrough valleys deep and over walls.\nYour love is strong, your light is true,\nShow me how to walk in you.",
                "language": "Hindi",
                "status": "ready"
            },
            {
                "title": "Peaceful Journey",
                "content": "Walk gently on this sacred ground,\nLet love be your only sound.\nThe path ahead is clear to see,\nWith faith as our companions free.",
                "language": "English",
                "status": "ready"
            }
        ]
        
        project_row = conn.execute(text("SELECT id FROM projects WHERE slug = :slug LIMIT 1"), {"slug": "demo-project"}).fetchone()
        if project_row:
            project_id = str(project_row.id)
        else:
            # Get the first project's ID
            result = conn.execute(text("SELECT id FROM projects ORDER BY created_at DESC LIMIT 1")).fetchone()
            if result:
                project_id = str(result.id)
            else:
                print("⚠️ No projects found, skipping lyrics insertion")
                return
        
        # Insert each lyric with a unique UUID
        for lyr in sample_lyrics:
            conn.execute(text("""
                INSERT INTO lyrics (id, project_id, title, content, language, status)
                VALUES (:id, :project_id, :title, :content, :language, :status)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": str(uuid4()),
                "project_id": project_id,
                **lyr
            })
        
        conn.commit()
        print(f"✓ Inserted {len(sample_lyrics)} sample lyrics")

if __name__ == "__main__":
    seed_database()
    print("\n🎉 Database seeded successfully!")
