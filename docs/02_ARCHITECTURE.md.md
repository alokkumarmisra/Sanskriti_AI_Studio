# ARCHITECTURE.md

## Architecture

Sanskriti AI Studio follows a Modular Monolith Architecture.

The application consists of independent modules that communicate only through defined interfaces.

No module may directly access another module's internal implementation.

---

# Technology Stack

Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui

Backend
- Python
- FastAPI

Database
- PostgreSQL
- SQLAlchemy

AI
- LM Studio
- ComfyUI

Media
- FFmpeg

---

# High Level Architecture

User

↓

Frontend

↓

REST API

↓

Services

↓

Repositories

↓

Database


AI Requests

↓

AI Service

↓

Workers

↓

LM Studio

↓

ComfyUI

↓

FFmpeg

---

# Project Structure

Sanskriti_AI_Studio/

docs/

frontend/

backend/

workers/

shared/

database/

scripts/

tests/

docker/

---

# Frontend Structure

frontend/

src/

app/

pages/

features/

components/

layouts/

hooks/

services/

api/

store/

types/

utils/

assets/

styles/

---

# Backend Structure

backend/

app/

api/

core/

services/

repositories/

models/

schemas/

ai/

workers/

middleware/

dependencies/

utils/

---

# Layer Responsibilities

Frontend

Responsible for UI only.

No business logic.

No database access.

No AI processing.

---

API

Receives requests.

Validates input.

Calls Services.

Returns responses.

Nothing else.

---

Services

Contains all business logic.

Coordinates repositories.

Coordinates AI.

Never communicates with UI.

---

Repositories

Database access only.

No business logic.

---

Models

Database entities.

---

Schemas

Request/Response DTOs.

---

AI

Communicates with

LM Studio

ComfyUI

Future AI Providers

---

Workers

Long running tasks.

Image generation.

Video generation.

Exports.

Queue processing.

---

Utils

Reusable helper functions only.

---

Shared

Common constants.

Shared models.

Enums.

Utilities.

No business logic.

---

# Dependency Rules

Allowed

Frontend

↓

API

↓

Services

↓

Repositories

↓

Database

Allowed

Services

↓

AI

↓

Workers

↓

Providers

Forbidden

Frontend → Database

Frontend → Repository

Frontend → AI

API → Database

API → Workers

Repository → UI

Repository → AI

Worker → Database Direct

Models → Services

Schemas → Repository

---

# Communication Rules

Modules communicate only through

Public Services

Public APIs

Never access internal module files.

---

# Feature Modules

Every feature should follow

Feature

↓

API

↓

Service

↓

Repository

↓

Database

---

# AI Module

All AI providers must implement a common interface.

Example

Generate Text

Generate Prompt

Generate Image

Generate Video

Future AI providers should require zero changes to business logic.

---

# Configuration

All configuration must come from

.env

No hardcoded paths.

No hardcoded URLs.

No hardcoded credentials.

---

# Logging

Every error must be logged.

Every AI request should be logged.

Every background job should be logged.

---

# Error Handling

Never expose internal exceptions.

Return standardized API responses.

---

# Security

JWT Authentication

Input Validation

Parameterized SQL

Secrets only in .env

---

# File Rules

One class per file.

One responsibility per class.

Avoid files larger than 400 lines.

Avoid methods larger than 40 lines.

---

# Naming Rules

Folders

lowercase

Files

snake_case (Python)

PascalCase (React Components)

Variables

camelCase

Classes

PascalCase

Constants

UPPER_CASE

---

# Development Rules

Never redesign architecture.

Never move folders.

Never rename folders.

Never rename APIs.

Never duplicate business logic.

Never bypass layers.

Modify only required files.

---

# Architecture Principles

Separation of Concerns

Dependency Injection

SOLID

DRY

KISS

YAGNI

---

# Future Extensions

Plugin System

Multiple AI Providers

Multiple Image Engines

Multiple Video Engines

Cloud Synchronization

Workflow Marketplace

Agent Marketplace

---

# Architecture Authority

This document defines the architecture.

All future development must follow this document.

No AI may violate these rules.