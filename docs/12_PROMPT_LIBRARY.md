# Sanskriti AI Studio — Prompt Library

**Version:** 1.0  
**Status:** Active  
**Last Updated:** 2026-07-30

## 1. Universal Development Prompt

```text
Before modifying any code:

1. Read all project documentation in the required order.
2. Read the current task.
3. Inspect the existing implementation.
4. Identify what already exists.
5. Do not duplicate existing functionality.
6. Implement only the requested milestone.
7. Run relevant tests.
8. Run frontend lint and build.
9. Run backend validation.
10. Fix root causes of failures.
11. Update required documentation.
12. Provide a detailed final report.
13. Do not automatically start the next milestone.
```

## 2. Debugging Prompt

```text
Diagnose the actual root cause before changing code.

Do not assume:
- Empty database
- Missing configuration
- CORS
- Frontend bug
- Backend bug

Verify:
1. Backend status.
2. Database connection.
3. API response.
4. HTTP status.
5. Browser network request.
6. Console errors.
7. CORS.
8. Request URL.
9. Request method.
10. Response schema.

Fix the root cause and verify again.
```

## 3. Frontend Feature Prompt

```text
Inspect existing frontend architecture before implementation.

Reuse:
- Existing routes.
- Existing API client.
- Existing TanStack Query setup.
- Existing UI components.
- Existing styling.

Do not:
- Introduce a new framework.
- Duplicate API clients.
- Add mock data as the source of truth.
- Redesign unrelated pages.

Verify:
- Loading.
- Error.
- Empty state.
- Success state.
- Browser refresh.
- Console errors.
- Network errors.
- npm run lint.
- npm run build.
```

## 4. Backend Feature Prompt

```text
Inspect existing:
- SQLAlchemy models.
- Pydantic schemas.
- Routers.
- Services.
- Repositories.
- Database session management.

Reuse existing architecture.

Do not create duplicate APIs or database connections.

Verify through Swagger where applicable.
```

## 5. Database Seed Prompt

```text
Diagnose the API first.

If GET endpoint returns HTTP 200 with [], the API is working and the database may simply be empty.

Inspect actual SQLAlchemy models and relationships.

Create 3–5 realistic development records for each relevant existing table.

Requirements:
- Valid foreign keys.
- No orphan records.
- Valid enums.
- Required fields populated.
- Idempotent execution.
- No duplicate unique values.
- No schema changes unless explicitly required.

Verify database relationships and APIs after seeding.
```

## 6. Documentation Prompt

```text
Read all documentation.

After implementation:
- Update current task.
- Append AI context.
- Append completed tasks.
- Update next task.
- Append changelog.

Never erase historical information.

Record exact implementation and validation results.
```

## 7. Testing Prompt

```text
Test the actual behavior.

Run:
- Backend validation.
- API verification.
- Frontend lint.
- Frontend build.
- Browser verification where applicable.

If failures occur:
1. Diagnose root cause.
2. Fix.
3. Re-run.
4. Repeat.

Do not suppress errors.
Do not claim PASS without verification.
```

## 8. AI Agent Prompt

```text
You are a specialized development agent.

Read project documentation first.

You must:
- Work only within assigned scope.
- Inspect existing code.
- Reuse existing architecture.
- Report actual results.
- Never claim success without verification.
- Never perform destructive Git operations without approval.

Return:
- Status.
- Files created.
- Files modified.
- Tests.
- Validation.
- Issues.
- Next recommendation.
```

## 9. Qwen 3.5 Rule Prompt

```text
Qwen 3.5 is TEXT-ONLY.

Never send:
- Images.
- Screenshots.
- Browser screenshots.
- Image URLs.
- Image files.
- Base64 image data.

If visual analysis is required, use a separate vision-capable model.

Do not add image input to Qwen 3.5 unless the project's architecture explicitly changes and the model is verified to support it.
```

## 10. Git Bash Prompt

```text
Provide Git commands specifically for Git Bash.

Do not provide PowerShell or Command Prompt syntax unless explicitly requested.

Before destructive Git operations, explain the impact and require explicit confirmation.
```
