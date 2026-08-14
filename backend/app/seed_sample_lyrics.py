# Script to insert sample lyrics directly into database

from uuid import uuid4
from app.core.database import engine
from sqlalchemy import text

def seed_lyrics():
    """Insert sample project and lyrics into the database."""
    
    with engine.connect() as conn:
        # First create a project if it doesn't exist
        result = conn.execute(text("""
            INSERT INTO projects (id, name, description, project_type, status, slug)
            VALUES (:id, :name, :description, :project_type, :status, :slug)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": str(uuid4()),
            "name": "Sample Project",
            "description": "A sample project for testing",
            "project_type": "general",
            "status": "active",
            "slug": "sample-project"
        })
        
        # Get the first project ID (most recent one)
        row = conn.execute(text("""
            SELECT id FROM projects 
            WHERE slug = 'sample-project' 
            ORDER BY created_at DESC 
            LIMIT 1
        """)).fetchone()
        
        if not row:
            print("⚠️ No sample project found")
            return
        
        project_id = str(row.id)
        print(f"✓ Found project ID: {project_id[:8]}...")
        
        # Sample lyrics to insert
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
        
        # Insert each lyric with a unique UUID
        for lyr in sample_lyrics:
            conn.execute(text("""
                INSERT INTO lyrics (id, project_id, title, content, language, status)
                VALUES (:id, :project_id, :title, :content, :language, :status)
            """), {
                "id": str(uuid4()),
                "project_id": project_id,
                **lyr
            })
        
        conn.commit()
        print(f"✓ Inserted {len(sample_lyrics)} sample lyrics into project: {project_id[:8]}...")
    
    print("\n🎉 Sample lyrics seeded successfully!")

if __name__ == "__main__":
    seed_lyrics()
