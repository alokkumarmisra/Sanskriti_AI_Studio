# MILESTONE 06.01 — Database Foundation

## Summary
Establish the foundational database schema and structure for Sanskriti AI Studio.

## Detailed Description
This milestone establishes the core database architecture including:
- Project configuration tables
- User management tables
- Lyrics storage
- Search indexes
- Audit logs

## Business Objective
Enable persistent, structured storage for all application data while supporting scalable growth and efficient retrieval operations.

## Scope

**In Scope:**
- Core project schema design
- User authentication tables
- Lyrics content tables
- Search index structures
- Database migration framework

**Out of Scope:**
- UI/UX implementation
- API endpoint creation (Milestone 06.02)
- Authentication middleware (Milestone 06.05)

## Prerequisites
- [ ] Backend development environment configured
- [ ] Alembic migration setup initialized
- [ ] Database connection string configured

## Dependencies
- Upstream: None (foundation milestone)
- Downstream: MILESTONE 06.02 — Backend APIs
- External: PostgreSQL/SQLite database instance

---

## Functional Requirements

1. **Project Configuration Table**
   - Store global project settings
   - Support dynamic configuration updates
   
2. **User Management Tables**
   - User accounts with authentication data
   - Session management
   - Permission roles

3. **Lyrics Content Tables**
   - Song lyrics storage
   - Metadata (artist, album, year)
   - Tags and categories

4. **Search Index Table**
   - Full-text search support
   - Search history logging

5. **Audit Log Table**
   - Track data modifications
   - User activity logging

## Technical Requirements

1. **Schema Design**
   - Normalized database design (3NF)
   - Appropriate indexing strategies
   - Foreign key constraints where applicable

2. **Migration Support**
   - Alembic migration scripts
   - Rollback capability for each migration
   - Version tracking

3. **Data Types**
   - Use appropriate SQL types for each field
   - Unicode support for text fields (UTF-8)

4. **Connection Pooling**
   - Configure connection pool settings
   - Handle connection lifecycle properly

## Acceptance Criteria

1. Database schema created with all core tables
2. Alembic migration scripts generated and validated
3. Migration commands run successfully (`alembic upgrade head`)
4. All foreign key relationships properly defined
5. Indexes created for query performance
6. Data integrity constraints enforced

## Validation Steps

1. Execute `alembic revision --autogenerate -m "Initial schema"`
2. Run `alembic upgrade head`
3. Verify all tables exist: `SELECT table_name FROM information_schema.tables;`
4. Check indexes: `SELECT indexname FROM pg_indexes WHERE tablename = 'projects';`
5. Validate constraints work with test data

## Documentation Requirements
- [ ] Migration guide created
- [ ] Data dictionary documented
- [ ] API reference updated (Milestone 06.02)

## Estimated Tasks

1. Analyze project requirements for data model
2. Design ER diagram for core entities
3. Create Alembic revision for initial schema
4. Write migration script with up/down functions
5. Test migration with sample data
6. Document schema in `docs/03_DATABASE_DESIGN.md`
7. Update API specification (Milestone 06.02)

## Related APIs
- `/api/v1/projects` - Project configuration endpoints
- `/api/v1/users` - User management endpoints
- `/api/v1/lyrics` - Lyrics CRUD endpoints

## Database Changes

```sql
-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lyrics table
CREATE TABLE IF NOT EXISTS lyrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255),
    album VARCHAR(255),
    year INTEGER,
    content TEXT,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Search indexes
CREATE TABLE IF NOT EXISTS search_indexes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    results JSONB NOT NULL,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Frontend Changes
- None at this milestone

## Backend Changes
- [ ] `backend/app/models.py` - Add model definitions
- [ ] `backend/app/database.py` - Configure database connection
- [ ] `alembic/versions/` - Migration scripts

## Testing Requirements
1. Unit tests for database connection handling
2. Integration tests for CRUD operations on each table
3. Migration rollback test
4. Constraint violation test (duplicate keys, invalid foreign keys)

## Completion Definition
Milestone 06.01 is complete when:
- All database tables are created and documented
- Alembic migrations run successfully without errors
- Database connection pooling is configured
- Data model matches `docs/03_DATABASE_DESIGN.md`

---

## Implementation Notes

### Migration Strategy
```python
# Example migration structure in alembic/versions/
# 06_01_initial_schema.py
def upgrade():
    op.create_table('projects', ...)
    op.create_table('users', ...)
    # ... other tables

def downgrade():
    op.drop_table('projects')
    op.drop_table('users')
    # ... drop in reverse order
```

### Indexing Strategy
- Primary keys on all tables (UUID)
- Composite indexes on frequently queried columns
- Full-text search indexes for lyrics content

---

*Generated by Milestone Knowledge Base - STEP 22.1*
