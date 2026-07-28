# WORKFLOWS.md

## Workflow Principles

Every workflow belongs to one Project.

Each workflow is independent.

Each step creates a Job.

Jobs may run sequentially or in parallel.

Every step can be restarted.

---

# Standard Workflow

Project

↓

Input

↓

AI Processing

↓

Assets

↓

Output

---

# Workflow 1 - Create Project

User

↓

Create Project

↓

Save Project

↓

Open Dashboard

---

# Workflow 2 - Lyrics

Create Project

↓

Import Lyrics

or

Write Lyrics

↓

Save Lyrics

---

# Workflow 3 - Scene Generation

Lyrics

↓

LM Studio

↓

Generate Scenes

↓

Review

↓

Edit

↓

Save

---

# Workflow 4 - Prompt Generation

Scenes

↓

Prompt Template

↓

LM Studio

↓

Generate Prompts

↓

Review

↓

Edit

↓

Save

---

# Workflow 5 - Image Generation

Prompts

↓

Queue

↓

ComfyUI

↓

Generated Images

↓

Review

↓

Regenerate (Optional)

↓

Approve

---

# Workflow 6 - Video Generation

Approved Images

↓

Camera Motion

↓

Transitions

↓

Video Clips

↓

Merge Clips

↓

Draft Video

---

# Workflow 7 - Audio

Song

↓

Voice

↓

Background Music

↓

Synchronization

↓

Audio Track

---

# Workflow 8 - Final Render

Draft Video

↓

Audio

↓

Subtitles (Optional)

↓

FFmpeg

↓

Final Video

---

# Workflow 9 - Export

Final Video

↓

Select Resolution

↓

Export

↓

Save

---

# Workflow 10 - Queue

Create Job

↓

Pending

↓

Running

↓

Completed

or

Failed

or

Cancelled

---

# Workflow 11 - Assets

Import

↓

Store Metadata

↓

Attach to Project

↓

Use in Workflow

---

# Workflow 12 - AI Providers

Select Provider

↓

Load Model

↓

Run Task

↓

Return Result

---

# Workflow 13 - Error Recovery

Job Failed

↓

Log Error

↓

Retry

or

Cancel

---

# Workflow Rules

Every workflow belongs to one Project.

Every generated file belongs to one Scene.

Every Scene belongs to one Lyrics document.

Every Job produces Logs.

Every Output is stored as an Asset.

---

# Parallel Processing

Allowed

Generate Images

Generate Videos

Upscaling

Exports

Forbidden

Database Migration

Project Deletion

Configuration Update

---

# Retry Policy

Network Error

Retry

Provider Busy

Retry

Validation Error

Stop

Authentication Error

Stop

---

# User Approval Points

Before Image Generation

Before Video Generation

Before Export

---

# Workflow Authority

Business workflows must remain stable.

Implementation may change.

Workflow order must not change without approval.
