#!/usr/bin/env python3
"""
Seed data script for Sanskriti AI Studio development environment.

This script creates deterministic, idempotent seed data for testing and development.
Usage: cd d:/Sanskriti_AI_Studio/backend && python scripts/seed_data.py

The seed operation is idempotent - running it multiple times will not create duplicates.
"""

import sys
from pathlib import Path
from sqlalchemy import text, select

# Add backend to path (where the 'app' module exists)
SCRIPT_DIR = Path(__file__).resolve().parent  # backend/scripts
BACKEND_ROOT = SCRIPT_DIR.parent  # backend
sys.path.insert(0, str(BACKEND_ROOT))


def main():
    """Main entry point for seeding data."""
    
    print("=" * 70)
    print("SANSCRITI AI STUDIO - SEED DATA SCRIPT")
    print("=" * 70)
    print()

    # Get raw database connection and keep open for all operations
    from app.core.database import engine
    
    conn = engine.connect()
    conn.execution_options(isolation_level="AUTOCOMMIT")
    
    try:
        # Check if projects already exist using raw SQL (idempotency check)
        result = conn.execute(text("SELECT COUNT(*) FROM projects WHERE name IS NOT NULL AND name != ''"))
        count = result.scalar() or 0
        
        if count > 0:
            print(f"WARNING: {count} project(s) already exist. Skipping seed operation.")
            print("To reset, run this script after clearing the database or dropping the 'projects' table.")
            return 0
        
        print("=" * 70)
        print("CREATING SEED DATA")
        print("=" * 70)
        print()

        # Create projects data as SQL insert statements (5 realistic projects)
        seed_sql = text("""
        INSERT INTO projects (id, name, slug, description, owner, project_type, status, created_at, updated_at, deleted_at, specs) VALUES 
            ('e1f2a3b4-c5d6-7890-abcd-ef1234567890', 'API Documentation Portal', 'api-docs', 'Documentation for developer APIs and reference guides.', NULL, 'documentation', 'completed', NOW(), NOW(), NULL, '{}'),
            ('f2e3a4b5-c6d7-8901-bcde-f23456789012', 'Computer Vision Model Analysis', 'computer-vision-research', 'Research on video content analysis and scene detection.', NULL, 'research', 'in_progress', NOW(), NOW(), NULL, '{}'),
            ('e3f4a5b6-c7d8-9012-cdef-345678901234', 'Content Generation Platform', 'content-gen-platform', 'AI platform for automated video summaries.', NULL, 'product', 'in_progress', NOW(), NOW(), NULL, '{}'),
            ('f4e5a6b7-c8d9-0123-def0-456789012345', 'Team Collaboration Tools', 'team-collab-tools', 'Internal tool for video production workflows.', NULL, 'general', 'draft', NOW(), NOW(), NULL, '{}'),
            ('e5f6a7b8-c9d0-1234-ef01-567890123456', 'Audio Processing Pipeline Evaluation', 'audio-processing-eval', 'Evaluation of audio processing for transcripts.', NULL, 'research', 'completed', NOW(), NOW(), NULL, '{}');
        """)
        
        # Execute the insert via raw SQL
        conn.execute(seed_sql)
        conn.commit()
        
        print("Created 5 test projects via SQL insert.")
        print()

        # Query and display created projects using raw SQL
        query = text("SELECT id, name, slug, description, project_type, status FROM projects ORDER BY name")
        result = conn.execute(query)
        
        for row in result.mappings():
            print(f"Project: {row['name']}")
            print(f"  ID: {row['id']}")
            print(f"  Slug: {row['slug']}")
            print(f"  Description: {row['description'] or '(no description)'}")
            print(f"  Type: {row['project_type']}")
            print(f"  Status: {row['status']}")
            print()

        print("=" * 70)
        print("SEED OPERATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())