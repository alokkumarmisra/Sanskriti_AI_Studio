# Sanskriti AI Studio — Project Story

**Version:** 1.0  
**Status:** Active  
**Last Updated:** 2026-07-30

## 1. Project Vision

Sanskriti AI Studio is a local-first, AI-assisted movie production studio designed to transform devotional lyrics, songs, stories, and creative concepts into cinematic videos.

The long-term vision is to provide a professional production workflow covering:

- Project creation and management
- Lyrics and text ingestion
- AI-assisted text analysis
- Story and scene planning
- Scene prompt generation
- Image generation
- Video generation
- Asset management
- Review and regeneration
- Audio/video synchronization
- Movie assembly
- Rendering and export
- Version history
- Resumable workflows
- Multi-project management
- AI-agent-assisted software development
- Plugin architecture

The system prioritizes local AI execution wherever practical.

## 2. Core Production Workflow

The intended production workflow is:

```text
Creative Input
    ↓
Project Creation
    ↓
Lyrics / Story / Audio
    ↓
Text Analysis
    ↓
Narrative Planning
    ↓
Scene Breakdown
    ↓
Scene Prompt Generation
    ↓
Image Generation
    ↓
Image Review
    ↓
Video Generation
    ↓
Video Review
    ↓
Upscaling / Processing
    ↓
Audio Synchronization
    ↓
Movie Assembly
    ↓
Final Rendering
    ↓
Export
```

Each stage should be modular and independently testable.

## 3. AI-Assisted Development

Sanskriti AI Studio is itself developed with AI-assisted software engineering.

AI coding assistants and project agents must:

1. Read project documentation.
2. Understand the current architecture.
3. Read the current task.
4. Inspect existing code.
5. Implement only the requested milestone.
6. Test the implementation.
7. Fix root causes of failures.
8. Update documentation.
9. Report exact results.
10. Suggest the next task without automatically implementing it.

The documentation is the project's source of truth.

## 4. Technology Direction

### Frontend

- React
- TypeScript
- Vite
- TailwindCSS
- shadcn/ui
- TanStack Query

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic

### Database

- PostgreSQL

### Local AI and Media

- LM Studio
- Local LLMs
- ComfyUI
- Image generation models
- Video generation models such as Wan family models
- FFmpeg

## 5. Local-First Philosophy

The project is designed to eventually support a complete local production pipeline:

```text
User PC
├── Sanskriti AI Studio
├── PostgreSQL
├── LM Studio
├── ComfyUI
├── Local AI Models
└── FFmpeg
```

The core production workflow should not depend on cloud AI once the required local models and software are installed.

## 6. Qwen 3.5 Constraint

Qwen 3.5 is currently used as a text-only LLM in this project.

Never send the following to Qwen 3.5:

- Images
- Screenshots
- Browser screenshots
- Image URLs
- Image files
- Base64 image data

If visual analysis is required, use a separate vision-capable model.

The vision workflow must remain separate:

```text
Visual Input
    ↓
Vision Model
    ↓
Text / Structured Analysis
    ↓
Coding / Testing Agent
```

## 7. Development Environment

The current development environment includes a Windows PC with approximately:

- NVIDIA RTX 3060 12GB
- Intel Core i7-14700F
- 32GB RAM

The project should remain optimized for local execution and should avoid unnecessarily large model requirements when smaller suitable models can perform the task.

## 8. Current Project State

The Projects foundation has been implemented through Milestone 6.5:

- Milestone 6.1 — Database Foundation: Completed
- Milestone 6.2 — Projects Backend APIs: Completed
- Milestone 6.3 — Projects Frontend UI: Completed
- Milestone 6.4 — Seed Data and API Verification: Completed
- Milestone 6.5 — Project Detail and Project Management UI: Completed

The current repository uses a freshly initialized Git history and the primary branch is `master`.

## 9. Ultimate Goal

The ultimate goal is to create a professional, modular, local AI movie production platform that can turn devotional and creative content into cinematic productions while also using specialized AI agents to accelerate its own development.

Every implementation should move toward that vision without introducing unnecessary complexity.
