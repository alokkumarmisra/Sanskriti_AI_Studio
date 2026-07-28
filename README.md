# Sanskriti AI Studio

A professional desktop application for creating AI-generated videos from lyrics or scripts.

## Architecture

Modular Monolith with separate frontend, backend, workers, and shared modules.

### Technology Stack

**Frontend**
- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui

**Backend**
- Python
- FastAPI

**Database**
- PostgreSQL
- SQLAlchemy

**AI**
- LM Studio
- ComfyUI

**Media**
- FFmpeg

## Project Structure

```
Sanskriti_AI_Studio/
├── docs/                    # Documentation
│   ├── 00_PROJECT.md       # Project overview
│   ├── 01_AGENTS.md        # Development rules
│   ├── 02_ARCHITECTURE.md  # Architecture specification
│   ├── 03_DATABASE.md      # Database design
│   ├── 04_API.md          # API specifications
│   ├── 05_WORKFLOWS.md    # Workflow definitions
│   └── 06_ROADMAP.md      # Development roadmap
├── frontend/               # React application
│   ├── src/
│   │   ├── app/           # App-level components
│   │   ├── pages/         # Page routes
│   │   ├── features/      # Feature modules
│   │   ├── components/    # Reusable UI components
│   │   ├── layouts/       # Layout components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── services/      # API and external service calls
│   │   ├── api/           # API client
│   │   ├── store/         # State management
│   │   ├── types/         # TypeScript type definitions
│   │   ├── utils/        # Utility functions
│   │   ├── assets/       # Static assets
│   │   └── styles/       # Global styles
│   ├── package.json
│   └── vite.config.ts
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core configuration
│   │   ├── services/     # Business logic
│   │   ├── repositories/ # Data access layer
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Request/response DTOs
│   │   ├── ai/          # AI provider integration
│   │   ├── workers/     # Background task handlers
│   │   ├── middleware/  # Middleware functions
│   │   ├── dependencies/# Dependency injection
│   │   └── utils/       # Utility functions
│   ├── pyproject.toml
│   └── Dockerfile
├── workers/               # Long-running tasks
├── shared/                # Shared constants, enums, utilities
├── database/              # Database migrations and seeds
├── scripts/               # Automation scripts
├── tests/                 # Test suites
├── docker/                # Docker configuration
└── .env.example          # Environment variables template