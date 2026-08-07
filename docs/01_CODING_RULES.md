# Sanskriti AI Studio — Coding Rules

**Version:** 1.0  
**Status:** Active  
**Last Updated:** 2026-07-30

## 1. General Rules

All code must be:

- Production-oriented
- Modular
- Maintainable
- Type-safe where applicable
- Testable
- Documented when behavior is non-obvious
- Consistent with the existing architecture

Do not rewrite working code without a clear reason.

Do not introduce duplicate functionality.

Do not implement future milestones unless explicitly instructed.

## 2. Existing Code First

Before creating a new file or component:

1. Search the repository.
2. Identify existing functionality.
3. Reuse existing services, components, utilities and patterns.
4. Extend existing code when appropriate.

Never create a second implementation of an existing feature.

## 3. Naming

Use clear descriptive names.

Python:

- `snake_case` for functions and variables.
- `PascalCase` for classes.
- `UPPER_SNAKE_CASE` for constants.

TypeScript/React:

- `camelCase` for variables and functions.
- `PascalCase` for components and types.
- Use descriptive names.

Avoid abbreviations unless they are universally understood.

## 4. Frontend Rules

Use:

- React
- TypeScript
- Existing routing
- Existing UI components
- TanStack Query for server state where already established

Do not:

- Hardcode API data as the source of truth.
- Add mock data as a replacement for working APIs.
- Duplicate API clients.
- Introduce another UI framework.
- Redesign unrelated screens.

All API calls should use the existing API architecture.

## 5. Backend Rules

Use:

- FastAPI
- Pydantic
- SQLAlchemy
- Existing service/repository architecture

Keep routers thin.

Business logic belongs in services.

Database access belongs in repositories or the established data-access layer.

Do not put complex business logic directly in API routes.

## 6. Database Rules

Use:

- PostgreSQL
- SQLAlchemy models
- Alembic migrations

Never:

- Modify the database manually when a migration is required.
- Create duplicate tables.
- Invent relationships without documenting them.
- Delete production data automatically.
- Hardcode database credentials.

Development seed data must be deterministic and idempotent.

## 7. API Rules

Every API must have:

- Clear request validation.
- Clear response schema.
- Appropriate HTTP status codes.
- Meaningful error handling.

Do not create APIs outside the specification unless explicitly instructed.

Avoid breaking existing API contracts.

## 8. Error Handling

Never suppress errors just to make tests pass.

Always:

1. Identify the root cause.
2. Fix the root cause.
3. Re-run the failing operation.
4. Verify the fix.

Errors should provide useful information to the user and developer.

## 9. Configuration

Never hardcode:

- Passwords
- API keys
- Secrets
- Machine-specific absolute paths
- Production credentials

Use environment configuration.

## 10. AI Rules

Qwen 3.5 is TEXT-ONLY.

Never send images or screenshots to Qwen 3.5.

For visual analysis, use a separate vision-capable model.

AI integrations must be isolated behind service or adapter layers where practical.

## 11. Git Rules

The user's preferred Git shell is Git Bash.

When providing Git commands to the user, provide Git Bash commands.

Do not recommend destructive Git operations without explicit confirmation.

Never automatically:

- Delete `.git`
- Force push
- Reset history
- Delete branches
- Recreate the repository

## 12. Documentation Rules

Whenever implementation changes:

- Update AI context.
- Record completed work.
- Update the active task.
- Update the next task.
- Append changelog entries.

Never erase historical records from append-only documents.

## 13. Testing Rules

At minimum, validate relevant areas:

```text
Backend
↓
Database
↓
API
↓
Frontend
↓
Lint
↓
Build
```

Test the actual behavior, not just whether code compiles.

## 14. Minimal Change Principle

Make the smallest safe change that fully solves the requested problem.

Do not refactor unrelated code during a milestone.

## 15. Definition of Done

A task is complete only when:

- Implementation is finished.
- Existing functionality remains working.
- Relevant tests pass.
- Lint/build pass where applicable.
- Documentation is updated.
- Remaining issues are explicitly reported.
