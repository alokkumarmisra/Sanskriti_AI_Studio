# Sanskriti AI Studio — Database Design

**Version:** 1.0  
**Status:** Active  
**Last Updated:** 2026-07-30

## 1. Purpose

This document describes the database architecture and rules.

The actual SQLAlchemy models and migrations are authoritative for implemented fields.

Do not invent fields based only on this document.

## 2. Database

Primary database:

```text
PostgreSQL
```

ORM:

```text
SQLAlchemy
```

Migration tool:

```text
Alembic
```

## 3. Core Design Principles

- Use normalized relational structures where appropriate.
- Use foreign keys for relationships.
- Enforce required fields at the database/application level.
- Avoid orphan records.
- Use migrations for schema changes.
- Keep seed data idempotent.
- Do not hardcode credentials.

## 4. Project Entity

The Project entity is the primary root entity for production work.

Conceptually:

```text
Project
├── id
├── name
├── description
├── status
├── created_at
└── updated_at
```

Only fields that actually exist in the implemented SQLAlchemy model should be used by application code.

## 5. Project Relationships

The long-term model may relate Projects to:

- Scenes
- Assets
- Prompts
- Jobs

Conceptually:

```text
Project
  ├── 1:N Scenes
  ├── 1:N Assets
  ├── 1:N Prompts
  └── 1:N Jobs
```

The actual schema is authoritative.

## 6. UUID Strategy

Where UUID primary keys are used:

- Generate IDs using the established application/database strategy.
- Never hardcode random UUIDs into production logic.
- Seed scripts may use deterministic IDs if compatible with the existing schema.

## 7. Foreign Keys

Every child record must reference a valid parent.

Never create orphan records.

When deleting parent records, follow the actual configured relationship and cascade behavior.

## 8. Seed Data

Development seed data must be:

- Realistic
- Deterministic where practical
- Idempotent
- Relationally valid
- Safe to execute repeatedly

Seed order must respect dependencies:

```text
Parent
 ↓
Child
 ↓
Grandchild
```

## 9. Database Migrations

All schema changes must use Alembic.

Workflow:

```text
Modify SQLAlchemy Model
 ↓
Create Migration
 ↓
Review Migration
 ↓
Apply Migration
 ↓
Verify Database
```

Do not manually alter production schema.

## 10. Metadata

Metadata should be stored in structured database columns or JSON fields only where appropriate.

Avoid storing arbitrary unstructured information when a proper relational field is required.

## 11. Media Storage

Large files should normally be stored in filesystem/object storage.

The database should store:

- File path/reference
- Media type
- Size
- Status
- Generation metadata
- Relationships

## 12. Versioning

Future asset and scene versions should preserve history rather than silently overwrite important production results.

Versioning implementation must be introduced through a dedicated milestone.

## 13. Current Database Milestones

Completed:

- Database foundation
- Project model and schema
- Project API persistence
- Development seed data

Current application data must be verified against the actual migrations and SQLAlchemy models before adding new schema features.
