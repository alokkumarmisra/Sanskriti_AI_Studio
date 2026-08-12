"""Authentication service for user management and JWT handling."""

from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import text

from app.core.database import engine


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(plain_password) == hashed_password


def generate_jwt_payload(user_id: str, email: str, role: str) -> dict:
    """Generate JWT payload structure (simplified for demo)."""
    now = datetime.utcnow()
    exp = now + timedelta(minutes=15)
    
    return {
        "sub": user_id,
        "email": email,
        "roles": [role],
        "exp": int(exp.timestamp()),
        "iat": int(now.timestamp()),
    }


def generate_refresh_token() -> str:
    """Generate a secure refresh token."""
    import secrets
    return secrets.token_urlsafe(256)


class AuthService:
    """Service for authentication operations."""

    def __init__(self):
        self.engine = engine

    def register_user(self, email: str, password: str, first_name: str | None = None,
                      last_name: str | None = None) -> dict:
        """Register a new user."""
        with self.engine.connect() as conn:
            # Check if email already exists
            result = conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email.lower().strip()}
            )
            existing_user = result.fetchone()

            if existing_user:
                raise ValueError("Email already registered")

            # Hash password
            password_hash = hash_password(password)

            # Create user
            conn.execute(
                text("""
                    INSERT INTO users (id, email, password_hash, first_name, last_name, role, is_active, created_at, updated_at)
                    VALUES (:id, :email, :password_hash, :first_name, :last_name, 'viewer', true, NOW(), NOW())
                """),
                {
                    "id": str(uuid4()),
                    "email": email.lower().strip(),
                    "password_hash": password_hash,
                    "first_name": first_name,
                    "last_name": last_name,
                }
            )
            conn.commit()

            # Fetch created user
            result = conn.execute(
                text("SELECT id, email, role, is_active FROM users WHERE email = :email"),
                {"email": email.lower().strip()}
            )
            row = result.fetchone()

            return {
                "success": True,
                "data": {
                    "id": row.id,
                    "email": row.email,
                    "role": row.role,
                    "is_active": row.is_active,
                },
                "message": "User registered successfully"
            }

    def login(self, email: str, password: str) -> dict:
        """Authenticate user and return tokens."""
        with self.engine.connect() as conn:
            # Find user
            result = conn.execute(
                text("SELECT id, email, password_hash, role FROM users WHERE email = :email"),
                {"email": email.lower().strip()}
            )
            row = result.fetchone()

            if not row or not verify_password(password, row.password_hash):
                raise ValueError("Invalid credentials")

            # Generate JWT payload
            jwt_payload = generate_jwt_payload(row.id, row.email, row.role)

            # Generate refresh token
            refresh_token = generate_refresh_token()
            
            # Create session record
            expires_at = datetime.utcnow() + timedelta(days=7)
            conn.execute(
                text("""
                    INSERT INTO auth_sessions (id, user_id, refresh_token, expires_at, ip_address, created_at)
                    VALUES (:id, :user_id, :refresh_token, :expires_at, :ip_address, NOW())
                """),
                {
                    "id": str(uuid4()),
                    "user_id": row.id,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at,
                    "ip_address": None,
                }
            )
            conn.commit()

            return {
                "success": True,
                "data": jwt_payload,
                "message": "Login successful"
            }

    def logout(self, refresh_token: str) -> dict:
        """Invalidate a refresh token."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("DELETE FROM auth_sessions WHERE refresh_token = :refresh_token"),
                {"refresh_token": refresh_token}
            )
            rows_deleted = result.rowcount

            return {
                "success": True,
                "data": None,
                "message": "Logout successful" if rows_deleted > 0 else "No active session found"
            }

    def get_profile(self, user_id: str) -> dict:
        """Get current user profile."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, email, first_name, last_name, role, is_active FROM users WHERE id = :id"),
                {"id": user_id}
            )
            row = result.fetchone()

            if not row:
                raise ValueError("User not found")

            return {
                "success": True,
                "data": {
                    "id": row.id,
                    "email": row.email,
                    "first_name": row.first_name,
                    "last_name": row.last_name,
                    "role": row.role,
                    "is_active": row.is_active,
                },
                "message": "Profile retrieved successfully"
            }

    def update_profile(self, user_id: str, first_name: str | None = None,
                       last_name: str | None = None) -> dict:
        """Update user profile."""
        with self.engine.connect() as conn:
            # Verify user exists
            result = conn.execute(
                text("SELECT id FROM users WHERE id = :id"),
                {"id": user_id}
            )
            if not result.fetchone():
                raise ValueError("User not found")

            update_fields = []
            values = {"id": user_id, "updated_at": datetime.utcnow()}

            if first_name is not None:
                update_fields.append(text("first_name = :first_name"))
                values["first_name"] = first_name
            if last_name is not None:
                update_fields.append(text("last_name = :last_name"))
                values["last_name"] = last_name

            set_clause = ", ".join(str(f) for f in update_fields)
            conn.execute(
                text(f"UPDATE users SET {set_clause}, updated_at = NOW() WHERE id = :id"),
                values
            )
            conn.commit()

            return {
                "success": True,
                "data": None,
                "message": "Profile updated successfully"
            }

    def change_password(self, user_id: str, old_password: str, new_password: str) -> dict:
        """Change user password."""
        with self.engine.connect() as conn:
            # Find user
            result = conn.execute(
                text("SELECT id, password_hash FROM users WHERE id = :id"),
                {"id": user_id}
            )
            row = result.fetchone()

            if not row or not verify_password(old_password, row.password_hash):
                raise ValueError("Current password is incorrect")

            # Update password
            new_hash = hash_password(new_password)
            conn.execute(
                text("UPDATE users SET password_hash = :password_hash WHERE id = :id"),
                {"password_hash": new_hash, "id": user_id}
            )
            conn.commit()

            return {
                "success": True,
                "data": None,
                "message": "Password changed successfully"
            }
