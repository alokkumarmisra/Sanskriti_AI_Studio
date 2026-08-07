# Sanskriti AI Studio — API Specification

**Version:** 1.0  
**Status:** Active  
**Last Updated:** 2026-07-30

## 1. Purpose

This document defines the API conventions and current Project API contract.

The actual FastAPI implementation and Pydantic schemas are authoritative for exact field names.

## 2. API Architecture

```text
Frontend
 ↓
HTTP REST
 ↓
FastAPI Router
 ↓
Service
 ↓
Repository
 ↓
PostgreSQL
```

## 3. API Rules

All APIs should:

- Validate input.
- Return typed responses.
- Use appropriate HTTP status codes.
- Provide meaningful errors.
- Avoid exposing internal database details.

## 4. Project Endpoints

The Project API currently supports the Project management workflow.

Expected operations:

```text
GET    /projects
GET    /projects/{project_id}
POST   /projects
PUT/PATCH /projects/{project_id}
DELETE /projects/{project_id}
```

The exact update method must follow the implemented backend.

## 5. GET Projects

Purpose:

Return the list of Projects.

Expected successful empty response:

```json
[]
```

An empty database is not an API failure.

## 6. GET Project by ID

Purpose:

Return a single Project.

Expected behavior:

- `200` when found.
- Appropriate `404` when not found.
- Appropriate server error when backend/database failure occurs.

## 7. CREATE Project

Purpose:

Create a new Project.

The request must contain all required fields according to the actual Pydantic schema.

The API must validate:

- Required fields
- Data types
- Valid enum values
- Uniqueness rules where applicable

## 8. UPDATE Project

Purpose:

Update an existing Project.

The API must:

- Validate input.
- Return the updated Project.
- Preserve database integrity.
- Return an appropriate not-found response when the Project does not exist.

## 9. DELETE Project

Purpose:

Delete a Project.

The backend must respect configured database relationship and cascade rules.

The frontend must request confirmation before deletion.

## 10. API Error Handling

Common cases:

```text
400 Bad Request
404 Not Found
409 Conflict
422 Validation Error
500 Internal Server Error
```

Only return statuses appropriate to the actual error.

## 11. CORS

The backend must allow the configured frontend development origin according to environment configuration.

Do not use overly permissive CORS in production.

## 12. API Verification

Swagger should be used to verify API behavior during development.

Minimum Project API verification:

- GET list
- GET by ID
- CREATE
- UPDATE
- DELETE

## 13. Frontend Integration

The frontend must use the established API client.

Do not create direct fetch calls in components if an API abstraction already exists.

## 14. Future API Areas

Future APIs may include:

- Scenes
- Assets
- Prompts
- Jobs
- AI generation
- Rendering

Do not implement these APIs until their milestones are active.
