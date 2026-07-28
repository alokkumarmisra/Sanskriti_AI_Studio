# Sanskriti AI Studio

# AI Development Documentation

Version: 1.0

---

# Purpose

Welcome to the Sanskriti AI Studio project.

This project is developed using AI-assisted software engineering.

Every AI coding assistant (Qwen3-Coder, GPT, Claude, Copilot, Gemini, etc.) **MUST read the project documentation before generating or modifying any code.**

The documentation is the **single source of truth** for this project.

Never skip any document.

Always read them in the exact order shown below.

---

# Documentation Reading Order

## Step 1 - Project Vision

Read

docs/00_PROJECT_STORY.md

Purpose

Understand

- Project vision
- Long-term goals
- Technology stack
- Overall objectives
- Expected workflow

---

## Step 2 - Coding Standards

Read

docs/01_CODING_RULES.md

Purpose

Understand

- Coding standards
- Naming conventions
- Folder structure
- Clean Architecture principles
- Design patterns
- Error handling rules

---

## Step 3 - System Architecture

Read

docs/02_SYSTEM_ARCHITECTURE.md

Purpose

Understand

- Overall system architecture
- Backend architecture
- Frontend architecture
- AI service architecture
- Background workers
- File storage
- Communication flow

---

## Step 4 - Database Design

Read

docs/03_DATABASE_DESIGN.md

Purpose

Understand

- PostgreSQL schema
- Entity relationships
- UUID strategy
- Metadata storage
- Versioning strategy

---

## Step 5 - API Specification

Read

docs/04_API_SPECIFICATION.md

Purpose

Understand

- REST APIs
- Request models
- Response models
- Service responsibilities
- API versioning

Never create APIs outside this specification unless instructed.

---

## Step 6 - Development Roadmap

Read

docs/05_ROADMAP.md

Purpose

Understand

- Milestones
- Development phases
- Current progress
- Future roadmap

Never implement future milestones unless instructed.

---

## Step 7 - AI RULES

Read

docs/07_AI_RULES.md

Purpose

Understand

- Milestones
- Development phases
- Current progress
- Future roadmap

Never implement future milestones unless instructed.

---

## Step 8 - Current Sprint

Read

docs/06_CURRENT_TASK.md

Purpose

Understand

- Current sprint
- Current implementation
- Acceptance criteria
- Current milestone

Implement ONLY this task.

---

## Step 9 - Development Guidelines

Read

docs/07_DEVELOPMENT_GUIDELINES.md

Purpose

Understand

- Development workflow
- Git workflow
- Testing strategy
- Documentation policy
- Code review process

---

## Step 10 - Current AI Context

Read

docs/08_AI_CONTEXT.md

Purpose

Understand

- Current implementation status
- Recent decisions
- Pending work
- Current architecture state

Continue development from the latest state.

Never restart the project.

---

## Step 10 - Completed Tasks

Read

docs/09_COMPLETED_TASKS.md

Purpose

Understand

- Completed features
- Completed APIs
- Completed database changes
- Completed UI work

Avoid implementing completed work again.

---

## Step 11 - Development Backlog

Read

docs/10_NEXT_TASK.md

Purpose

Understand

- Upcoming work
- Priority order
- Pending features

After completing CURRENT_TASK.md, continue with the highest priority task.

---

## Step 12 - Project History

Read

docs/11_CHANGELOG.md

Purpose

Understand

- Version history
- Bug fixes
- Refactoring
- Feature history

Append new changes after implementation.

---

## Step 13 - Prompt Library

Read

docs/12_PROMPT_LIBRARY.md

Purpose

Understand

- Reusable prompts
- AI workflows
- Coding prompts
- Documentation prompts

Reuse these prompts whenever applicable.

---

## Step 14 - Architecture Decisions

Read

docs/13_DECISIONS.md

Purpose

Understand

- Why architectural decisions were made
- Approved technologies
- Rejected alternatives
- Long-term technical direction

Never violate these decisions without explicit approval.

---

## Step 15 - AI Operating Instructions

Read

docs/99_AI_INSTRUCTIONS.md

Purpose

Understand

- Mandatory AI behavior
- Coding policies
- Documentation requirements
- Development rules

These instructions override any default AI behavior.

---

# Mandatory Development Workflow

Every development session MUST follow this order:

1. Read documentation
2. Understand architecture
3. Review CURRENT_TASK.md
4. Review existing code
5. Implement backend
6. Implement database changes
7. Implement frontend
8. Test implementation
9. Update documentation
10. Verify acceptance criteria
11. Suggest the next task

Never skip any step.

---

# Mandatory Build Verification

Every implementation must finish with:

Backend Build

↓

Frontend Build

↓

Database Migration Check

↓

Application Startup

↓

Error Analysis

↓

Automatic Fix

↓

Rebuild

↓

Restart

↓

Repeat until successful


# Documentation Update Policy

Whenever code changes, Append the affected documentation. Never overwrite append-only documents.

Possible documents include:

- docs/02_SYSTEM_ARCHITECTURE.md
- docs/03_DATABASE_DESIGN.md
- docs/04_API_SPECIFICATION.md
- docs/05_ROADMAP.md
- docs/06_CURRENT_TASK.md
- docs/08_AI_CONTEXT.md
- docs/09_COMPLETED_TASKS.md
- docs/10_NEXT_TASK.md
- docs/11_CHANGELOG.md


Update project documentation following the documentation policy.

Requirements:

- Never overwrite append-only documents.
- Append new AI context.
- Append completed tasks.
- Append changelog entries.
- Update only the relevant section of NEXT_TASK.md.
- Replace CURRENT_TASK.md with the newly active task.
- Preserve all historical information.

---

# Technology Stack

## Frontend

- React
- TypeScript
- Vite
- TailwindCSS
- shadcn/ui

## Backend

- FastAPI
- Python
- SQLAlchemy
- Alembic

## Database

- PostgreSQL

## AI Services

- LM Studio
- ComfyUI
- Wan2.1
- FFmpeg

---

# Core Principles

Always produce

- Production-ready code
- Modular architecture
- Reusable components
- Clean code
- Type-safe code
- Well-documented code
- Scalable implementation

Never produce

- Demo code
- Placeholder implementations
- Hardcoded paths
- Hardcoded ports
- Duplicate logic
- Unused code

---

# Ultimate Goal

Build a professional, fully offline AI Movie Production Studio capable of transforming devotional lyrics into cinematic videos using local AI models.

The system should eventually support:

- One-click project creation
- Scene generation
- Image generation
- Video generation
- Review dashboards
- Movie rendering
- Resume workflow
- Regeneration
- Version history
- Multi-project management
- Plugin architecture
- Production deployment

Every implementation should contribute toward this long-term vision.