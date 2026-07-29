"""Test script to verify Lyrics integration works correctly."""

import sys
sys.path.insert(0, '.')

# Import models directly (not through app package)
from app.models.project import Base as ProjectBase
from app.models.lyrics import Base as LyricsBase

print("=== Backend Model Verification ===")
print(f"ProjectBase tables: {[t.name for t in ProjectBase.metadata.sorted_tables]}")
print(f"LyricsBase tables: {[t.name for t in LyricsBase.metadata.sorted_tables]}")

# Verify models have correct relationship
from app.models.project import Project
from app.models.lyrics import Lyrics

print(f"\n=== Relationship Verification ===")
print(f"Project has lyrics attribute: {hasattr(Project, 'lyrics')}")
print(f"Lyrics has project attribute: {hasattr(Lyrics, 'project')}")
print(f"Lyrics.project relationship: {Lyrics.project}")

# Test service imports
try:
    from app.services.lyrics_service import LyricsService
    print(f"\n=== Service Import ===")
    print(f"LyricsService imported successfully")
except Exception as e:
    print(f"\n=== Service Import Error ===")
    print(f"Error: {e}")

# Test repository imports
try:
    from app.repositories.lyrics_repository import LyricsRepository
    print(f"\n=== Repository Import ===")
    print(f"LyricsRepository imported successfully")
except Exception as e:
    print(f"\n=== Repository Import Error ===")
    print(f"Error: {e}")

# Test schema imports
try:
    from app.schemas.project import LyricsRead, LyricsCreate, LyricsUpdate
    print(f"\n=== Schema Import ===")
    print(f"LyricsRead imported successfully")
    print(f"LyricsCreate imported successfully")
    print(f"LyricsUpdate imported successfully")
except Exception as e:
    print(f"\n=== Schema Import Error ===")
    print(f"Error: {e}")

# Test API route imports
try:
    from fastapi import FastAPI
    app = FastAPI()
    from app.api.projects.routes import router as projects_router
    print(f"\n=== API Routes Import ===")
    print(f"Projects routes imported successfully")
except Exception as e:
    print(f"\n=== API Routes Import Error ===")
    print(f"Error: {e}")

print("\n=== All Verifications Complete ===")
