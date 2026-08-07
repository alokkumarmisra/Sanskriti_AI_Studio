# Sanskriti AI Studio — Development Roadmap

**Version:** 1.0  
**Status:** Active  
**Last Updated:** 2026-07-30

## 1. Roadmap Purpose

This roadmap defines the high-level development direction.

The active task is always controlled by:

```text
docs/06_CURRENT_TASK.md
```

The next planned task is controlled by:

```text
docs/10_NEXT_TASK.md
```

Do not implement future roadmap items automatically.

## 2. Foundation Phase

### Milestone 6.1 — Database Foundation

Status: COMPLETED

Objectives:

- Establish database structure.
- Configure SQLAlchemy.
- Configure Alembic.
- Implement Project persistence.

### Milestone 6.2 — Projects Backend APIs

Status: COMPLETED

Objectives:

- Project CRUD APIs.
- Pydantic schemas.
- Service/repository integration.
- API validation.

### Milestone 6.3 — Projects Frontend UI

Status: COMPLETED

Objectives:

- Projects list.
- Backend integration.
- TanStack Query integration.
- Loading/error/empty states.

### Milestone 6.4 — Seed Data and API Verification

Status: COMPLETED

Objectives:

- Diagnose Project API issue.
- Verify backend/database.
- Fix CORS issue where required.
- Create idempotent development seed data.
- Verify Swagger.
- Verify frontend.

### Milestone 6.5 — Project Detail and Project Management UI

Status: COMPLETED

Objectives:

- Project detail route.
- Project detail data.
- Edit/update.
- Delete confirmation.
- Navigation.
- Loading/error states.
- Responsive UI.
- Validation.

## 3. Future Roadmap Direction

The exact next milestone must be selected based on the current architecture and documented in `10_NEXT_TASK.md`.

Likely future areas include:

```text
Project Workspace
 ↓
Scene Management
 ↓
Lyrics / Audio Input
 ↓
Scene Planning
 ↓
Prompt Management
 ↓
AI Text Generation
 ↓
Image Generation
 ↓
Video Generation
 ↓
Asset Review
 ↓
Job Management
 ↓
Movie Assembly
 ↓
Rendering / Export
```

These are directional goals, not automatic implementation instructions.

## 4. AI Agent Development Roadmap

The development automation system is being built incrementally.

Completed or established runtimes include:

- Coding Agent Runtime
- Testing Agent Runtime
- Documentation Agent Runtime

Future agent capabilities may include:

- Master Orchestrator
- Planning Agent
- Debugging Agent
- Review Agent
- Git Agent
- Deployment Agent

Each agent should be implemented as a dedicated task.

## 5. Production Roadmap

Long-term:

1. Project workspace.
2. Creative input management.
3. Scene planning.
4. Prompt generation.
5. Image generation.
6. Video generation.
7. Review.
8. Regeneration.
9. Audio synchronization.
10. Movie rendering.
11. Export.
12. Versioning.
13. Multi-project management.
14. Plugin architecture.
15. Production deployment.

## 6. Roadmap Rule

Never skip directly to a future milestone unless explicitly requested.

Each milestone must:

- Have clear acceptance criteria.
- Preserve existing functionality.
- Be tested.
- Be documented.
