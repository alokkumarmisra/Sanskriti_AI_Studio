"""Simple import test for Lyrics integration."""

import sys
sys.path.insert(0, '.')

try:
    from app.models.lyrics import Lyrics
    print("[OK] Lyrics model imported successfully")
except Exception as e:
    print(f"[FAIL] Lyrics model import failed: {e}")
    sys.exit(1)

try:
    from app.models.project import Project
    print("[OK] Project model imported successfully")
except Exception as e:
    print(f"[FAIL] Project model import failed: {e}")
    sys.exit(1)

try:
    from app.schemas.project import LyricsRead, LyricsCreate, LyricsUpdate
    print("[OK] Lyrics schemas imported successfully")
except Exception as e:
    print(f"[FAIL] Lyrics schemas import failed: {e}")
    sys.exit(1)

try:
    from app.services.lyrics_service import LyricsService
    print("[OK] LyricsService imported successfully")
except Exception as e:
    print(f"[FAIL] LyricsService import failed: {e}")
    sys.exit(1)

try:
    from app.repositories.lyrics_repository import LyricsRepository
    print("[OK] LyricsRepository imported successfully")
except Exception as e:
    print(f"[FAIL] LyricsRepository import failed: {e}")
    sys.exit(1)

print("\n=== All Imports Successful ===")
