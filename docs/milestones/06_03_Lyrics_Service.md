# MILESTONE 06.03 — Lyrics Service

## Summary
Implement the lyrics service layer for content management and search integration.

## Detailed Description
This milestone builds the business logic layer that handles all lyrics-related operations, including:
- Content validation (copyright checks, length limits)
- Search index population
- Tag management
- Versioning for lyric updates

## Business Objective
Provide a robust lyrics management service that supports content creators while respecting copyright and quality standards.

## Scope

**In Scope:**
- Lyrics CRUD operations
- Tag management system
- Search index building
- Content validation layer
- History tracking for updates

**Out of Scope:**
- User authentication (Milestone 06.05)
- Frontend implementation (Milestone 06.06)
- Music streaming integration

## Prerequisites
- [ ] Milestone 06.02 — Backend APIs completed
- [ ] Search index schema created (Milestone 06.01)
- [ ] User management layer ready

## Dependencies
- Upstream: MILESTONE 06.02 — Backend APIs
- Downstream: MILESTONE 06.04 — Search Features
- External: No external dependencies (all data from existing tables)

---

## Functional Requirements

1. **Lyrics CRUD Service**
   - Create new lyrics entries
   - Update existing lyrics with version tracking
   - Delete lyrics (with soft delete option)
   - Fetch lyrics by ID or search term

2. **Tag Management**
   - Add/remove tags from lyrics
   - Tag suggestion based on content
   - Tag normalization (lowercase, no duplicates)

3. **Content Validation**
   - Character count limits
   - Minimum content length check
   - Profanity filter integration
   - Copyright warning for user-uploaded content

4. **Search Index Service**
   - Build/update search indexes on write
   - Delete from index when content removed
   - Support partial text matching

5. **History Service**
   - Track all lyric modifications
   - Maintain version history
   - Provide rollback capability

## Technical Requirements

1. **Service Pattern**
   - Separate service layer from route handlers
   - Dependency injection for database access
   - Async operations where applicable

2. **Validation Pipeline**
   ```python
   async def validate_lyrics(content: str, title: str) -> ValidationResult:
       # Check length limits
       # Check profanity (optional)
       # Validate metadata
   ```

3. **Search Integration**
   - Full-text search on lyrics content
   - Tag-based filtering
   - Sort by relevance/date

4. **Soft Delete**
   - `is_deleted` boolean flag
   - Archive old deleted content
   - Clean up old indexes periodically

## Acceptance Criteria

1. Lyrics create/update/delete operations work correctly
2. Tags are automatically normalized and deduplicated
3. Content validation catches invalid inputs
4. Search index updates immediately on write
5. Version history tracks all changes
6. Soft delete preserves data integrity

## Validation Steps

1. Test create lyric with valid content
2. Verify search index updated: `SELECT * FROM search_indexes;`
3. Test tag normalization: `{"tags": ["Pop", "POP"]}` → `["pop"]`
4. Test validation rejects empty content
5. Verify soft delete keeps original record
6. Check version history table for updates

## Documentation Requirements
- [ ] Service interface documented
- [ ] Error codes listed
- [ ] Usage examples added to API docs

## Estimated Tasks

1. Define LyricsService interface
2. Implement CRUD methods
3. Add tag management logic
4. Build validation pipeline
5. Implement search index updates
6. Create version history tracking
7. Write unit tests for each method

## Related APIs
- `/api/v1/lyrics` - All lyrics endpoints
- Service layer: `backend/app/services/lyrics_service.py`

## Database Changes

```sql
-- Lyrics content versions (for history tracking)
CREATE TABLE IF NOT EXISTS lyric_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lyric_id UUID REFERENCES lyrics(id) ON DELETE CASCADE,
    content_hash VARCHAR(64),  -- SHA-256 of content for deduplication
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    user_id UUID REFERENCES users(id)
);

-- Tag usage tracking
CREATE TABLE IF NOT EXISTS lyric_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lyric_id UUID REFERENCES lyrics(id) ON DELETE CASCADE,
    tag_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Frontend Changes
- Add lyrics management UI (Milestone 06.06)
- Tag editor component
- Search interface integration

## Backend Changes
- [ ] `backend/app/services/lyrics_service.py` - Service layer
- [ ] `backend/app/services/tag_service.py` - Tag management
- [ ] `backend/app/schemas/lyrics.py` - Pydantic schemas
- [ ] `backend/app/repositories/lyrics_repo.py` - Data access

## Testing Requirements
1. Unit tests for each service method
2. Integration test for full CRUD flow
3. Validation edge case tests
4. Search index update verification
5. Tag normalization tests
6. Soft delete behavior tests

## Completion Definition
Milestone 06.03 is complete when:
- LyricsService implemented with all methods working
- Tag management system operational
- Content validation pipeline functional
- Search indexes updated on writes
- Version history tracking enabled

---

*Generated by Milestone Knowledge Base - STEP 22.1*
