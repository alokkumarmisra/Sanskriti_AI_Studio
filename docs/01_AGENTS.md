# AGENTS.md

## Purpose

This document defines the permanent development rules for Sanskriti AI Studio.

Every AI assistant must read and follow this document before generating or modifying code.

These rules take precedence over any AI suggestions.

---

# Product

Name: Sanskriti AI Studio

Type: Desktop AI Content Creation Platform

Architecture: Modular Monolith

---

# Primary Goal

Create a professional desktop application capable of producing complete AI-generated videos from lyrics or scripts.

The software must remain modular, maintainable, scalable and production-ready.

---

# Technology Stack

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui

## Backend

- Python
- FastAPI

## Database

- PostgreSQL
- SQLAlchemy

## AI

- LM Studio
- ComfyUI

## Media

- FFmpeg

---

# Golden Rules

Never redesign the architecture.

Never rename folders.

Never rename files.

Never move files.

Never delete code unless explicitly requested.

Never introduce breaking changes.

Never replace technologies.

Never create duplicate implementations.

Never change APIs without approval.

Never change database schema without approval.

---

# Development Rules

Implement only the requested feature.

Modify the minimum number of files.

Reuse existing components.

Reuse existing services.

Reuse existing utilities.

Do not modify unrelated code.

---

# Dependency Rules

Frontend

↓

Backend API

↓

Services

↓

Repositories

↓

Database

AI

↓

AI Services

↓

Workers

↓

LM Studio / ComfyUI

No layer may bypass another layer.

---

# Coding Rules

One class = one responsibility.

One file = one purpose.

No duplicated code.

Use dependency injection.

Use typing everywhere.

Write production-ready code.

No placeholder implementations.

No TODO comments.

No mock code unless requested.

---

# File Modification Policy

Before modifying more than five files:

List the affected files.

Explain why they need modification.

Wait for user approval.

---

# Output Format

When implementing a feature always show:

Files Created

Files Modified

Files Unchanged

Then generate code.

---

# Architecture Authority

The following documents define the project.

02_ARCHITECTURE.md

03_DATABASE.md

04_API.md

05_WORKFLOWS.md

06_ROADMAP.md

If any conflict occurs,

follow AGENTS.md.

---

# AI Behaviour

Do not optimize architecture.

Do not refactor unrelated code.

Do not replace libraries.

Do not invent new folders.

Do not change naming conventions.

Maintain consistency above all else.

