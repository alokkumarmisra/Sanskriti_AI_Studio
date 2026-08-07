# Sanskriti AI Studio — Architecture Decisions

**Version:** 1.0  
**Status:** Active  
**Last Updated:** 2026-07-30

> This document records architectural decisions. New decisions must be appended.

## ADR-001 — React + TypeScript Frontend

**Status:** Accepted

The frontend uses React and TypeScript.

Reason:

- Mature ecosystem.
- Type safety.
- Component architecture.
- Good compatibility with Vite.

## ADR-002 — Vite

**Status:** Accepted

Vite is used as the frontend build and development tool.

## ADR-003 — FastAPI Backend

**Status:** Accepted

FastAPI is used for the backend.

Reasons:

- Python ecosystem.
- Strong typing through Pydantic.
- Async support.
- Good API documentation.
- Suitable for AI integration.

## ADR-004 — PostgreSQL

**Status:** Accepted

PostgreSQL is the primary relational database.

## ADR-005 — SQLAlchemy + Alembic

**Status:** Accepted

SQLAlchemy is used for ORM/database access.

Alembic is used for migrations.

## ADR-006 — TanStack Query

**Status:** Accepted

TanStack Query is used for frontend server-state management where established.

## ADR-007 — Local-First AI

**Status:** Accepted

The project prioritizes local AI services.

Primary local AI tooling includes:

- LM Studio.
- ComfyUI.
- Local AI models.
- FFmpeg.

## ADR-008 — Qwen 3.5 Text-Only Integration

**Status:** Accepted

Qwen 3.5 is treated as a text-only LLM in the project.

Images must not be sent to it.

Visual analysis requires a separate vision-capable model.

## ADR-009 — Separate Vision Model

**Status:** Accepted in Principle

If browser screenshots or other images must be analyzed by AI, a separate vision-capable model must be used.

Architecture:

```text
Image
 ↓
Vision Model
 ↓
Text / Structured Result
 ↓
Application Agent
```

This keeps Qwen 3.5's text-only workflow intact.

## ADR-010 — Git Primary Branch

**Status:** Accepted

The current repository primary branch is:

```text
master
```

Do not rename or recreate the repository without explicit instruction.

## ADR-011 — Fresh Git History

**Status:** Accepted

The repository was freshly initialized after previous history was intentionally removed.

The current working code is the source of truth.

## ADR-012 — Documentation as Source of Truth

**Status:** Accepted

AI assistants must read project documentation before coding.

Documentation must be updated after implementation.

## ADR-013 — Specialized Development Agents

**Status:** Accepted

AI-assisted development is divided into specialized agent responsibilities.

Current completed runtimes include:

- Coding Agent.
- Testing Agent.
- Documentation Agent.

Future agents may include orchestration, review, Git and deployment capabilities.

## ADR-014 — No Automatic Future Milestones

**Status:** Accepted

An AI agent must not automatically implement future milestones.

It may recommend the next task, but implementation requires an explicit task/prompt.
