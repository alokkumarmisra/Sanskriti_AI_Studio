"""Script to create lyrics table manually."""

import psycopg2

conn = psycopg2.connect(
    host='localhost', 
    database='sanskriti_ai_studio', 
    user='postgres', 
    password='postgres'
)
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS lyrics;')
cur.execute('''CREATE TABLE lyrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(256),
    content TEXT NOT NULL,
    language VARCHAR(64) DEFAULT 'English',
    status VARCHAR(32) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);''')
cur.execute('CREATE INDEX idx_lyrics_project_id ON lyrics(project_id);')
conn.commit()
cur.close()
conn.close()

print('Lyrics table created successfully!')