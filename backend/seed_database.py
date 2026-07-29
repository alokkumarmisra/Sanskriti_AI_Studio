"""Script to seed database with dummy data for Projects and Lyrics."""

import uuid
from datetime import datetime

import psycopg2

# Database connection (matches alembic.ini)
DB_CONFIG = {
    "host": "localhost",
    "database": "sanskriti_ai_studio",
    "user": "postgres",
    "password": "postgres",
}


def get_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)


def create_projects(conn):
    """Create 10 projects with unique data."""
    conn.autocommit = True
    cursor = conn.cursor()
    
    project_names = [
        "Film Noir Detective",
        "Cyberpunk Future",
        "Romantic Comedy",
        "Horror Mansion",
        "War Epic",
        "Fantasy Quest",
        "Musical Theater",
        "Legal Thriller",
        "Sports Underdog",
        "Period Drama",
    ]
    
    project_descs = [
        "A gritty detective story in 1940s New York",
        "Neon-lit streets, corporate espionage, and AI rebellion",
        "Two strangers fall in love during a cross-country road trip",
        "A cursed estate where every room tells a dark story",
        "The untold story of soldiers from opposing sides finding peace",
        "A young wizard's journey to save the enchanted forest",
        "A Broadway star's redemption through unforgettable songs",
        "A defense attorney takes on an impossible case",
        "A small town team defies all odds to reach the championship",
        "The rise and fall of a wealthy family in Victorian England",
    ]
    
    project_types = [
        "narrative", "sci-fi", "comedy-romance", "horror", 
        "drama-war", "fantasy", "musical-drama", "legal-thriller", 
        "sports-drama", "period-drama"
    ]
    
    print("Creating 10 projects...")
    
    # Track used slugs to generate unique ones
    used_slugs = set()
    
    for idx, (name, desc, ptype) in enumerate(zip(project_names, project_descs, project_types)):
        # Generate slug from name (lowercase, replace spaces with -, remove special chars)
        slug = "".join(c.lower() if c.isalnum() else "-" for c in name.replace(" ", "-")).replace("--", "-").rstrip("-")
        
        # If slug already exists, append a number
        counter = 1
        while slug in used_slugs:
            slug = f"{slug}-{counter}"
            counter += 1
        
        cursor.execute(
            """INSERT INTO projects 
               (id, name, description, project_type, status, slug) 
               VALUES (%s, %s, %s, %s, 'active', %s)""",
            [str(uuid.uuid4()), name, desc, ptype, slug],
        )
        used_slugs.add(slug)

    conn.commit()
    print(f"Created {cursor.rowcount} projects")


def create_lyrics(conn):
    """Create 10 lyrics entries for each project (maintaining relationship)."""
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Get all project IDs
    cursor.execute("SELECT id FROM projects ORDER BY id")
    project_ids = [row[0] for row in cursor.fetchall()]

    print("Creating 10 lyrics entries per project...")
    
    # Define 10 unique titles and their associated content lines
    lyric_data = [
        ("The Detective's Confession", ["I never meant to hurt her", "She looked at me with such betrayal", "The rain washed away everything"]),
        ("Neon Dreams", ["The city sleeps but I cannot close my eyes", "Every neon sign is a whisper in the dark", "AI dreams of humanity it will never understand"]),
        ("First Love Again", ["You said forever but time moves on", "I still hear your laughter in empty streets", "Some wounds heal with seasons changing"]),
        ("The Haunting", ["She walks through walls I cannot cross", "Her ghost lives in every shadowed corner", "This house remembers everything we did"]),
        ("Letters from the Front", ["Today is the last day I'll see him alive", "I wrote what I should have said years ago", "Heroes don't always make it home"]),
        ("The Spell", ["The forest breathes in ancient tongues", "Magic flows through every leaf and stream", "I must find the heart before sunrise"]),
        ("Encores", ["The applause fades but the music lingers", "One more song for one more night", "Stars witness what few audiences see"]),
        ("Not Guilty", ["They say justice is blind to truth", "Evidence proves what they fear to hear", "I'll fight every lie in court today"]),
        ("Victory March", ["This town will stand tall after tomorrow", "Every player knows we can win tonight", "Dreams built on hope and sweat"]),
        ("Heritage", ["Gold is buried deep beneath the floorboards", "Secrets kept through three generations", "Legacy is what remains when wealth fades"]),
    ]
    
    # Create a pool of lyrics to cycle through for each project
    lyrics_pool = []
    for title, lines in lyric_data:
        content = f"{lines[0]} {lines[1]} {lines[2]}"
        lyrics_pool.append((title, content))
    
    print(f"Creating {len(project_ids) * 10} lyrics entries...")
    for project_id in project_ids:
        # Cycle through the lyric pool (create 10 lyrics per project)
        for idx, (title, content) in enumerate(lyrics_pool):
            cursor.execute(
                """INSERT INTO lyrics 
                   (id, project_id, title, content, language, status, created_at, updated_at) 
                   VALUES (%s, %s, %s, %s, 'English', 'active', %s, %s)""",
                [str(uuid.uuid4()), project_id, title, content, datetime.now().isoformat(), datetime.now().isoformat()],
            )
    
    conn.commit()
    print(f"Created {len(project_ids) * len(lyrics_pool)} lyrics entries")


def show_table_count(conn):
    """Display current table counts."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 'projects' as table_name, COUNT(*) as count 
        FROM projects
        UNION ALL
        SELECT 'lyrics' as table_name, COUNT(*) as count 
        FROM lyrics
    """)
    rows = cursor.fetchall()
    
    print("\n=== Database Seed Summary ===")
    for row in rows:
        print(f"{row['table_name']}: {row['count']} records")


def main():
    """Main function to seed the database."""
    conn = None
    try:
        conn = get_connection()
        print("Connected to PostgreSQL database")
        
        # Create projects first (parent table)
        create_projects(conn)
        
        # Then create lyrics (child table with FK to projects)
        create_lyrics(conn)
        
        # Show summary
        show_table_count(conn)
        
        print("\n✅ Database seeding completed successfully!")
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
