# Script to append lyrics CRUD endpoints to main.py

with open('backend/app/main_lyrics_crud.txt', 'r') as f:
    content = f.read().strip()[31:]  # Remove leading comment and blank line

with open('backend/app/main.py', 'a') as f:
    f.write('\n\n# ============================================\n# LYRICS CRUD ENDPOINTS (MILESTONE 7.2)\n# ============================================\n' + content)

print("Lyrics CRUD endpoints appended successfully!")
