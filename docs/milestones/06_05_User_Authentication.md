# MILESTONE 06.05 — User Authentication

## Summary
Implement user authentication and authorization system for the application.

## Detailed Description
This milestone establishes the security layer that enables:
- User registration and profile management
- Secure login with password hashing
- JWT-based token authentication
- Role-based access control (RBAC)
- Session management

## Business Objective
Provide a secure authentication system that protects user data while enabling personalized experiences through proper session management.

## Scope

**In Scope:**
- User registration and validation
- Login/logout operations
- Password hashing and verification
- JWT token generation and validation
- Role-based permissions
- Session timeout handling

**Out of Scope:**
- OAuth2 provider integration (Google, GitHub)
- Two-factor authentication (can be added later)
- Frontend authentication UI

## Prerequisites
- [ ] Milestone 06.04 — Search Features completed
- [ ] Users table created (Milestone 06.01)
- [ ] User routes defined (Milestone 06.02)
- [ ] Password hashing library configured

## Dependencies
- Upstream: MILESTONE 06.04 — Search Features
- Downstream: MILESTONE 06.06 — Project Workspace Dashboard
- External: JWT library, password hashing utilities (bcrypt/argon2)

---

## Functional Requirements

1. **Registration Flow**
   - `POST /api/v1/auth/register` - Create new user account
   - Validate email uniqueness
   - Hash password before storage
   - Send welcome email (optional)

2. **Login Flow**
   - `POST /api/v1/auth/login` - Authenticate user
   - Return JWT access token and refresh token
   - Set expiration times appropriately

3. **Token Management**
   - `POST /api/v1/auth/refresh` - Get new tokens
   - `POST /api/v1/auth/logout` - Invalidate current tokens
   - Token refresh before expiry (grace period)

4. **Role-Based Access Control**
   - User role: `viewer`, `editor`, `admin`
   - Permissions mapped to roles
   - Middleware for route protection

5. **Profile Management**
   - `GET /api/v1/auth/profile` - Get current user profile
   - `PUT /api/v1/auth/profile` - Update profile
   - Password change endpoint

## Technical Requirements

1. **JWT Token Structure**
   ```json
   {
       "sub": "uuid:user-id",
       "email": "user@example.com",
       "roles": ["editor"],
       "exp": 1730000000,
       "iat": 1729996400
   }
   ```

2. **Password Hashing**
   - Use bcrypt or argon2
   - Cost factor: bcrypt=12, argon2=memory=65536,times=3
   - Never store plain passwords

3. **Token Storage**
   - Access token: Short-lived (15 minutes)
   - Refresh token: Long-lived (7 days), stored securely
   - HttpOnly cookie or secure header-based transmission

4. **Session Cleanup**
   - Cron job to clean expired tokens
   - Delete inactive sessions after timeout

## Acceptance Criteria

1. User registration creates account with hashed password
2. Login returns valid JWT tokens
3. Protected routes reject requests without valid token
4. Password hashing verified (never plain text in DB)
5. Role-based access control working correctly
6. Token refresh works before expiry

## Validation Steps

1. Register new user, verify account created
2. Login with credentials, verify tokens returned
3. Access protected route without token - should be rejected
4. Access protected route with invalid token - should be rejected
5. Refresh tokens before expiry, verify new tokens issued
6. Verify password in database is hashed (bcrypt prefix)

## Documentation Requirements
- [ ] Authentication flow documented
- [ ] Token format specification
- [ ] Role definitions listed
- [ ] API docs updated with auth headers

## Estimated Tasks

1. Implement user registration endpoint
2. Create login/refresh/logout endpoints
3. Add JWT token generation and validation
4. Implement role-based middleware
5. Configure password hashing
6. Set up session cleanup cron job
7. Write authentication tests
8. Document authentication requirements

## Related APIs
- `/api/v1/auth/register` - User registration
- `/api/v1/auth/login` - User login
- `/api/v1/auth/refresh` - Token refresh
- `/api/v1/auth/logout` - User logout
- `/api/v1/auth/profile` - Get profile

## Database Changes

```sql
-- Add roles column to users (if not exists)
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'viewer';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Create sessions table for refresh tokens
CREATE TABLE IF NOT EXISTS auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for session cleanup queries
CREATE INDEX sessions_expires_idx ON auth_sessions(expires_at);
```

## Frontend Changes
- Login page component
- Registration form
- Password change modal
- Auth state management in frontend store

## Backend Changes
- [ ] `backend/app/auth.py` - Authentication logic
- [ ] `backend/app/middleware/auth.py` - JWT validation middleware
- [ ] `backend/app/routes/auth.py` - Auth endpoints
- [ ] `backend/app/schemas/auth.py` - Pydantic auth schemas
- [ ] `backend/services/auth_service.py` - Password hashing, token handling

## Testing Requirements
1. Unit tests for password hashing/unhashing
2. Unit tests for JWT encoding/decoding
3. Integration test for registration flow
4. Integration test for login flow
5. Role-based access control tests (all role combinations)
6. Token expiration and refresh tests
7. Concurrent authentication test (logout while logged in)

## Completion Definition
Milestone 06.05 is complete when:
- Registration creates valid user accounts with hashed passwords
- Login returns valid JWT tokens that expire correctly
- Protected routes properly reject invalid/missing tokens
- Role-based access control working for all roles
- Session cleanup cron job operational
- No authentication-related security vulnerabilities

---

*Generated by Milestone Knowledge Base - STEP 22.1*
