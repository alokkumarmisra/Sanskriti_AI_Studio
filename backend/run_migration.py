"""Run database migrations for Milestone 6.6."""
from sqlalchemy import text

def apply_migration(engine):
    """Apply users and auth_sessions table migration."""
    with engine.connect() as conn:
        print("=== Running Migration ===")
        
        # Create users table
        print("[OK] Creating users table...")
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(256) UNIQUE NOT NULL,
                    password_hash VARCHAR(256) NOT NULL,
                    first_name VARCHAR(128),
                    last_name VARCHAR(128),
                    role VARCHAR(32) DEFAULT 'viewer',
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    owned_project_ids VARCHAR(255) DEFAULT '[]'
                )
            """)
        )

        # Create auth_sessions table
        print("[OK] Creating auth_sessions table...")
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    refresh_token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    ip_address VARCHAR(45),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )

        # Create indexes
        print("[OK] Creating indexes...")
        conn.execute(text("CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON auth_sessions(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS sessions_expires_idx ON auth_sessions(expires_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS sessions_refresh_token_idx ON auth_sessions(refresh_token)"))

        conn.commit()
        print("[OK] Migration Complete\n")

if __name__ == "__main__":
    from app.core.database import engine
    apply_migration(engine)
