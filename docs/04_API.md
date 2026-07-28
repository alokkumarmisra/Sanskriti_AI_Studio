# API.md

## API Standard

Protocol: REST

Format: JSON

Authentication: JWT

Version: v1

Base URL

/api/v1

---

# Standard Response

Success

{
    "success": true,
    "data": {},
    "message": ""
}

Error

{
    "success": false,
    "message": "",
    "errors": []
}

---

# Authentication

POST /auth/login

POST /auth/logout

POST /auth/refresh

GET /auth/me

---

# Projects

GET /projects

GET /projects/{id}

POST /projects

PUT /projects/{id}

DELETE /projects/{id}

---

# Lyrics

GET /projects/{projectId}/lyrics

POST /projects/{projectId}/lyrics

PUT /lyrics/{id}

DELETE /lyrics/{id}

---

# Scenes

GET /projects/{projectId}/scenes

POST /projects/{projectId}/scenes/generate

PUT /scenes/{id}

DELETE /scenes/{id}

---

# Prompts

GET /projects/{projectId}/prompts

POST /projects/{projectId}/prompts/generate

PUT /prompts/{id}

POST /prompts/{id}/regenerate

---

# Images

GET /projects/{projectId}/images

POST /images/generate

POST /images/upscale

DELETE /images/{id}

---

# Videos

GET /projects/{projectId}/videos

POST /videos/generate

POST /videos/merge

DELETE /videos/{id}

---

# Audio

GET /projects/{projectId}/audio

POST /audio/import

DELETE /audio/{id}

---

# Assets

GET /projects/{projectId}/assets

POST /assets/upload

DELETE /assets/{id}

---

# AI Providers

GET /ai/providers

GET /ai/models

POST /ai/test

---

# Jobs

GET /jobs

GET /jobs/{id}

POST /jobs/{id}/cancel

---

# Queue

GET /queue

POST /queue/pause

POST /queue/resume

POST /queue/clear

---

# Export

POST /export/video

GET /export/history

DELETE /export/{id}

---

# Settings

GET /settings

PUT /settings

---

# Logs

GET /logs

---

# Health

GET /health

---

# HTTP Status

200 OK

201 Created

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error

500 Internal Server Error

---

# Validation Rules

Validate every request.

Never trust client input.

Return meaningful errors.

---

# Versioning

Current

/api/v1

Future

/api/v2

Never introduce breaking changes in the same version.

---

# API Rules

Use nouns instead of verbs.

Use plural resource names.

Keep endpoints consistent.

Use standard HTTP methods.

Return JSON only.

---

# API Authority

This document defines the public API.

Endpoints must remain backward compatible.

No endpoint should be renamed without approval.
