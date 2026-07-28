# PROJECT_STORY.md

# Sanskriti AI Studio

Version: 1.0
Author: Alok Misra
Status: In Development

---

# Project Vision

Sanskriti AI Studio is a complete offline AI Movie Production Suite that converts devotional lyrics into cinematic AI videos with a single click.

The software is designed for creators who want to generate professional-quality devotional videos without requiring any knowledge of AI models, ComfyUI workflows, or video editing.

The long-term vision is to become an all-in-one AI content creation platform capable of generating:

- Devotional Movies
- Bhajan Videos
- AI Music Videos
- Short Videos
- Animated Stories
- YouTube Videos
- Instagram Reels
- AI Advertisements
- Educational Videos
- Children's Stories
- Motivational Videos

Everything should be automated.

The user should only provide the lyrics (or story), then press one button, and the complete production pipeline should execute automatically.

No manual file handling should ever be required.

---

# Primary Goal

The application should work like a professional production studio.

Input:

Lyrics

↓

Output:

Complete 4K cinematic movie

---

# Design Philosophy

The application must be

Simple

Fast

Scalable

Production Ready

Modular

Offline First

Future Proof

Every module must be independent.

Every AI model should be replaceable.

No module should depend on a specific AI model.

---

# Complete Production Pipeline

User opens the application

↓

Creates a new project

↓

Pastes lyrics

↓

Clicks Generate Project

↓

LM Studio generates cinematic scenes

↓

Scene editor opens

↓

User can edit scenes if required

↓

ComfyUI generates images

↓

Images appear automatically

↓

User reviews images

↓

User regenerates selected images if needed

↓

Wan2.1 generates videos

↓

Videos appear automatically

↓

User reviews videos

↓

User regenerates selected videos if required

↓

FFmpeg combines all clips

↓

Background music is merged

↓

Final movie is generated

↓

User exports the movie

---

# Long-Term Features

The application will eventually support

Voice Cloning

Lip Sync

Character Consistency

Automatic Camera Movement

Automatic Prompt Improvement

Automatic Thumbnail Generation

Automatic Subtitle Generation

Automatic Translation

Multi-language Support

Automatic YouTube Upload

Cloud Rendering

Distributed Rendering

Multi GPU Support

Resume Failed Jobs

Workflow Templates

Plugin Marketplace

Model Manager

AI Agent Integration

Remote Rendering

API Support

---

# Technology Stack

Frontend

React

Vite

TypeScript

TailwindCSS

shadcn/ui

React Query

React Router

Backend

FastAPI

Python

SQLAlchemy

Alembic

Pydantic

PostgreSQL

Redis (future)

AI Models

LM Studio

Qwen3-Coder-30B

FLUX

Wan2.1

Future models

LTX Video

Hunyuan Video

Stable Diffusion

SDXL

Kokoro TTS

XTTS

Whisper

ComfyUI

Video Processing

FFmpeg

ImageMagick

Pillow

Automation

Background Jobs

Async Workers

Queue System

WebSocket Notifications

---

# AI Models

Scene Generation

LM Studio

Image Generation

ComfyUI

FLUX

Video Generation

Wan2.1

Future

LTX Video

Speech

Future

XTTS

Whisper

---

# Database

PostgreSQL

The application should never store important information in JSON files.

JSON files may be used only for caching.

The database is always the source of truth.

---

# Database Tables

Projects

Scenes

Images

Videos

WorkflowRuns

Jobs

Settings

Logs

Prompts

Models

Users (future)

Templates

---

# Folder Structure

Sanskriti_AI_Studio/

backend/

frontend/

database/

comfy/

workflows/

projects/

models/

ffmpeg/

logs/

temp/

exports/

docs/

tests/

---

# Project Structure

Each project contains

Project

↓

Scenes

↓

Images

↓

Videos

↓

Movie

↓

Export

---

# UI Layout

Left Sidebar

Projects

Dashboard

Models

Jobs

Logs

Settings

Center

Main Workspace

Right Panel

Properties

Prompt Editor

Preview

Bottom Panel

Logs

Queue

Notifications

---

# Dashboard

The dashboard should display

Projects

Running Jobs

GPU Usage

CPU Usage

RAM Usage

Disk Usage

Completed Videos

Failed Jobs

Recent Projects

Estimated Rendering Time

---

# Scene Workflow

Each scene contains

Scene Number

Lyrics

Narration

Visual Description

Camera

Lighting

Emotion

Duration

Image Prompt

Negative Prompt

Image Status

Video Status

Notes

---

# Image Workflow

Each image has

Generate

Preview

Approve

Reject

Regenerate

Upscale

Replace

Edit Prompt

History

---

# Video Workflow

Each video has

Generate

Preview

Approve

Reject

Regenerate

Change Motion Prompt

Extend Duration

Upscale

History

---

# Movie Workflow

Merge Clips

Transitions

Music

Fade In

Fade Out

Subtitles

Credits

Export

---

# Future AI Review System

The software should automatically detect

Blurry Images

Wrong Hands

Wrong Faces

Text in Image

Watermarks

Artifacts

Poor Composition

Low Resolution

Incorrect Character

The AI should recommend regeneration automatically.

---

# Background Job System

Every operation should execute as a background job.

Nothing should block the UI.

Jobs include

Generate Scenes

Generate Images

Generate Videos

Merge Movie

Export

Upload

Every job should support

Pause

Resume

Cancel

Retry

---

# Architecture

React UI

↓

FastAPI

↓

Business Layer

↓

Repository Layer

↓

PostgreSQL

↓

Background Workers

↓

LM Studio

↓

ComfyUI

↓

Wan2.1

↓

FFmpeg

---

# Coding Standards

Always write production-ready code.

Never generate placeholder code.

Never generate demo code.

Always use TypeScript strict mode.

Always use Python type hints.

Always use async functions.

Always separate frontend and backend.

Never duplicate logic.

Always write reusable components.

Always use repository pattern.

Always use dependency injection where appropriate.

Always validate API requests.

Always return proper HTTP status codes.

Always create Alembic migrations.

Always update API documentation.

Always write scalable code.

Always follow SOLID principles.

---

# UI Design

Modern

Minimal

Dark Mode

Responsive

Fast

Keyboard Friendly

Professional

Inspired by professional creative software.

---

# Performance Goals

The application should support

Unlimited projects

Thousands of scenes

Thousands of generated images

Thousands of videos

Background rendering

Automatic recovery after crash

Resume interrupted rendering

GPU acceleration

---

# Future AI Agents

Future versions will include specialized AI agents.

Project Manager Agent

Prompt Engineer Agent

Scene Director Agent

Image Reviewer Agent

Video Reviewer Agent

Movie Editor Agent

YouTube Publisher Agent

Every agent should communicate through APIs.

---

# Current Development Phase

Version

0.1

Current Priority

Build a stable production-ready architecture.

Current Goal

Develop a one-click workflow:

Paste Lyrics → Generate Scenes → Generate Images → Review Images → Generate Videos → Review Videos → Merge Movie → Export.

No feature should compromise scalability or maintainability.

---

# Success Criteria

A user should be able to:

1. Create a new project.
2. Paste lyrics.
3. Click "Generate".
4. Review AI-generated scenes.
5. Review generated images.
6. Review generated videos.
7. Export a cinematic movie.

The application should handle the rest automatically.

End of PROJECT_STORY.md