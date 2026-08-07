# Sanskriti AI Studio — AI Context

**Version:** 1.7  
**Status:** Active  
**Last Updated:** 2026-08-06

## STEP 23.2 — Vision Service & Model Router — COMPLETED

The Vision Service and Model Router provide centralized management for all vision model communication.

### Architecture Flow (STEP 23.2)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Vision     │     │   Vision    │     │  Model      │     │ LM Studio    │
│  Agent      │ →   │  Service    │ →   │  Router     │ →   │ Vision API   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘

Key Principles:
1. Vision Agent NEVER calls LM Studio directly
2. All model selection goes through Model Router
3. Qwen 3.5 remains TEXT-ONLY (never receives images)
4. Configuration is externalized (no hardcoded values)
5. Health monitoring with retry logic
6. Structured response normalization

```

### New Components (STEP 23.2)

#### 1. Model Router (`ai_agents/scripts/model_router.py`)
- Centralized router for managing and selecting AI models
- Provides `get_text_model()`, `get_vision_model()` methods
- Implements `health_check()` with 60s caching
- Supports `list_available_models()` for discovery
- Request logging for audit trail

#### 2. Vision Service (`ai_agents/scripts/vision_service.py`)
- Handles ALL LM Studio vision communication
- Implements retry logic with exponential backoff (default: 3 retries, 2x backoff)
- Timeout handling per request (default: 300s)
- Error classification and recovery
- Health monitoring via `/models` endpoint
- Image submission with base64 encoding

#### 3. Response Parser (`ai_agents/scripts/response_parser.py`)
- Normalizes Vision model responses into standardized format
- Extracts: Summary, Components, OCR text, Issues, Warnings, Confidence, Suggested Fixes
- Handles JSON and text-based responses
- Extracts structured data from unstructured responses

#### 4. Vision Configuration (`ai_agents/scripts/vision_config.py`)
- Centralized configuration system
- All values externalized via environment variables:
  - `LM_STUDIO_BASE_URL` (connection)
  - `CODING_MODEL` (text-only model, e.g., Qwen 3.5)
  - `VISION_MODEL` (vision model, e.g., Qwen2.5-VL)
  - `VISION_TIMEOUT`, `VISION_TEMPERATURE`, etc.
- Configuration validation with error reporting

### Standardized Response Format (STEP 23.2)

Vision responses are normalized to standardized schema:

```json
{
  "status": "success | error | warning",
  "summary": "Brief summary of findings",
  "model_used": "Model identifier used",
  "latency_ms": Request duration in milliseconds,
  "components": [{"type": "...", "description": "..."}],
  "ocr": "Extracted text content",
  "issues": [{"type": "...", "severity": "...", "message": "..."}],
  "warnings": ["Warning message 1", "Warning message 2"],
  "confidence": "High | Medium | Low",
  "suggested_fixes": ["Fix suggestion 1", "Fix suggestion 2"]
}
```

### Health Check Results

The Model Router implements automatic health checks:

- **LM Studio reachable** - Checks `/models` endpoint for availability
- **Vision model loaded** - Verifies vision model is available in LM Studio
- **Response time** - Measures latency with caching (60s expiry)
- **Connection status** - Maintains connection state, retries on temporary failures

### Logging Results

All requests are logged with:
- Request ID (for correlation)
- Model Used (from Router, never hardcoded)
- Start Time (ISO-8601 UTC)
- End Time (or None on failure)
- Duration (in milliseconds)
- Retry Count (before final failure)
- Errors (error messages for failed requests)
- Success Status

### Files Created for STEP 23.2

| File | Purpose |
|------|---------|
| `ai_agents/scripts/model_router.py` | Centralized model selection and routing |
| `ai_agents/scripts/vision_service.py` | All LM Studio vision communication |
| `ai_agents/scripts/response_parser.py` | Response normalization |
| `ai_agents/scripts/vision_config.py` | Externalized configuration system |
| `ai_agents/scripts/vision_agent_new.py` | Updated Vision Agent runtime (STEP 23.2) |

### Files Modified for STEP 23.2

- `docs/02_SYSTEM_ARCHITECTURE.md` - Added Section 14A (Vision Service & Model Router)
- `docs/08_AI_CONTEXT.md` - This file (updated with STEP 23.2 documentation)
- `docs/11_CHANGELOG.md` - Added STEP 23.2 changelog entry

---

## Runtime Recovery System (STEP 21.6) — COMPLETED

The Runtime Recovery System provides fault-tolerant recovery capabilities that can restore the autonomous runtime after failures without losing progress.

### Supported Failure Types

The system handles all common failure scenarios:

1. **LM Studio disconnect** - Reconnect strategy
2. **LLM timeout** - Retry with backoff
3. **Agent crash** - Restore from checkpoint
4. **Python exception** - Restore from checkpoint
5. **Runtime crash** - Full state restoration
6. **Backend unavailable** - Reconnect backend
7. **Frontend unavailable** - Reconnect frontend
8. **Database unavailable** - Manual intervention required
9. **User interruption** - Resume with confirmation
10. **OS restart** - Post-bootstrap resume
11. **Unexpected shutdown** - Restore from checkpoint

### Checkpoint System Features

- **Atomic writes** using temporary file + rename pattern prevents corruption
- **Versioned checkpoints** (v0, v1, v2, etc.) enable rollback capability
- **Integrity verification** via SHA-256 checksums detects corruption
- **Automatic cleanup** keeps only latest 3 versions to save disk space

### Recovery Manager Responsibilities

- Detect interrupted execution from any failure type
- Locate the latest valid checkpoint
- Validate checkpoint integrity before restore
- Restore runtime state (milestone, task, agent, status)
- Restore execution queue and history
- Resume execution safely after environment validation

### Safe Resume Process

Before resuming execution:

1. Verify LM Studio availability
2. Verify backend service availability
3. Verify frontend service availability
4. Verify database connection
5. Verify required documentation exists
6. Validate checkpoint integrity and recency
7. Only continue if all validations pass

### Failure Policies & Strategies

| Failure Type | Severity | Retryable | Strategy |
|-------------|----------|-----------|----------|
| LM Studio disconnect | Temporary | Yes | Reconnect |
| LLM timeout | Retryable | Yes | Retry with backoff |
| Agent crash | Retryable | Yes | Restore and resume |
| Python exception | Retryable | Yes | Restore and resume |
| Runtime crash | Retryable | Yes | Full state restore |
| Backend unavailable | Temporary | Yes | Reconnect backend |
| Frontend unavailable | Temporary | Yes | Reconnect frontend |
| Database unavailable | Permanent | No | Manual intervention required |
| User interruption | Non-retryable | No | Prompt resume with confirmation |
| OS restart | Permanent | No | Post-bootstrap resume |
| Unexpected shutdown | Retryable | Yes | Restore from checkpoint |

### Files Created for STEP 21.6

- `ai_agents/scripts/checkpoint_manager.py` - Checkpoint storage with atomic writes, versioning, and integrity verification
- `ai_agents/scripts/recovery_manager.py` - Recovery manager with failure detection, strategy mapping, state restoration, and safe resume
- `ai_agents/scripts/validate_recovery.py` - Validation script for testing recovery functionality

### Files Modified for STEP 21.6

- `docs/08_AI_CONTEXT.md` - Added Runtime Recovery System documentation (Section above)

---

## Validation Engine Architecture (STEP 21.7) — COMPLETED

The Validation Engine provides a comprehensive quality assurance system:

### Validation Pipeline Stages

1. **Planner Validation** - Verifies execution plans have required structure
2. **Coding Validation** - Syntax check for modified Python files
3. **Backend Build** - Validates pyproject.toml, pip dependencies, alembic migrations
4. **Frontend Build** - Validates package.json integrity and build process
5. **Lint** - ESLint and Pyright type checking
6. **Integration Tests** - Full test suite validation
7. **API Validation** - HTTP endpoint accessibility checks
8. **Database Validation** - PostgreSQL connectivity and schema verification
9. **Reviewer Validation** - Quality gate for completed work
10. **Documentation Validation** - Required docs existence and currency check
11. **Acceptance Criteria Validation** - Task acceptance criteria documented

### Status Types

- **PASS** - Stage passed successfully
- **FAIL** - Stage failed (blocking issue)
- **WARNING** - Non-blocking issue detected
- **BLOCKED** - Cannot proceed due to missing dependencies
- **SKIPPED** - Stage intentionally skipped (e.g., backend not running)

### Quality Score System

The Validation Engine calculates an overall quality score:

- Based on pass/fail ratio of each stage
- Build failures penalize most heavily (-25%)
- Test/Integration issues penalize moderately (-15%)
- Lint/API/Database warnings penalize lightly (-5%)
- Warnings provide small bonus points for early issue detection
- Score ranges from 0% to 100%

### Validation History

All validation results are persisted to `ai_agents/state/validation_history.json`:

- Successful validations (full reports)
- Failed validations (with failure reasons)
- Retry counts per stage
- Average durations per stage
- Common failures tracking for trend analysis

### Usage

```bash
# Run full validation pipeline
python ai_agents/scripts/validation_engine.py --task-id STEP217_VALIDATION --milestone VALIDATION_ENGINE

# Skip backend validation (when not running)
python ai_agents/scripts/validation_engine.py --skip-backend

# View results
# - Overall quality score displayed
# - Per-stage status and duration
# - Errors/warnings logged
# - History automatically recorded
```

### Files Created for STEP 21.7

- `ai_agents/scripts/validation_engine.py`

---

## Vision Agent Runtime (STEP 23.1) — COMPLETED

The Vision Agent Runtime provides independent visual analysis capabilities using Qwen2.5-VL via LM Studio. It is separate from the Coding Agent and never generates source code.

### Responsibilities

- Browser UI analysis from screenshots
- Screenshot understanding and description
- OCR text extraction
- Error message extraction
- Layout validation
- Visual regression testing
- UI element verification

### Vision Model Integration (STEP 23.1)

The Vision Agent uses Qwen2.5-VL via LM Studio for visual analysis:

```text
Browser/Source
  ↓ Screenshot
Vision Client (LMStudioVisionClient)
  ↓ Image + Prompt
Qwen2.5-VL Model (via LM Studio)
  ↓ Structured Response
VisionAgent Class
  ↓ Parsed Report
ai_agents/state/vision_report.json
```

### Vision Agent Capabilities (STEP 23.1)

The Vision Agent supports these analysis tasks:

1. **General Analysis** - Comprehensive UI screenshot description
2. **Component Detection** - Identify all UI components (buttons, forms, tables, images, etc.)
3. **OCR Extraction** - Extract all visible text from the image
4. **Error Detection** - Find and extract error messages/warnings
5. **Layout Analysis** - Analyze layout structure, alignment, hierarchy
6. **UI Verification** - Verify presence of specific UI elements
7. **Visual Regression** - Compare two screenshots for differences

### Files Created for STEP 23.1

- `ai_agents/scripts/vision_client.py` - LM Studio vision client with image processing
- `ai_agents/agents/vision.py` - VisionAgent class definition
- `ai_agents/scripts/vision_agent.py` - Main runtime script
- `ai_agents/communication_bus/vision.py` - Communication bus registration

### Files Modified for STEP 23.1

- `docs/02_SYSTEM_ARCHITECTURE.md` - Added Section 14 (Vision Agent Architecture)
- `docs/08_AI_CONTEXT.md` - Added Vision Agent Runtime documentation

---

## Completed Milestones

### AI Agent Runtime Progress

- **Coding Agent Runtime (STEP 12)** — COMPLETED
- **Testing Agent Runtime (STEP 13)** — COMPLETED
- **Documentation Agent Runtime (STEP 15)** — COMPLETED
- **Orchestrator Agent Runtime (STEP 16)** — COMPLETED
- **Planner Agent Runtime (STEP 17)** — COMPLETED
- **Debugging Agent Runtime (STEP 18)** — COMPLETED AND VERIFIED
- **Reviewer Agent Runtime (STEP 19)** — COMPLETED AND VERIFIED
- **Milestone Execution Manager (STEP 20)** — COMPLETED
- **Runtime Bootstrap (STEP 21.1)** — COMPLETED
- **Intelligent Context Manager (STEP 21.2)** — COMPLETED
- **Task Scheduler & Queue Manager (STEP 21.3)** — COMPLETED
- **Agent Communication Bus (STEP 21.4)** — COMPLETED
- **Human Approval Workflow (STEP 21.5)** — COMPLETED
- **Runtime Recovery System (STEP 21.6)** — COMPLETED
- **Validation Engine (STEP 21.7)** — COMPLETED
- **Vision Agent Runtime (STEP 23.1)** — COMPLETED AND VERIFIED
- **Vision Service & Model Router (STEP 23.2)** — COMPLETED

### 6.x Database Project Milestones

- 6.1 — Database Foundation — COMPLETED
- 6.2 — Projects Backend APIs — COMPLETED
- 6.3 — Projects Frontend UI — COMPLETED
- 6.4 — Database Seed Data and API Verification — COMPLETED
- 6.5 — Project Detail and Project Management UI — COMPLETED

---

## Environment Status

- LM Studio: Available (http://localhost:1234)
- Backend API: Available (http://localhost:8000)
- Frontend UI: Available (http://localhost:5173)
- Database: PostgreSQL configured
- Vision Agent: Ready (uses Qwen2.5-VL model via LM Studio)

---

## Documentation Loaded

All project documentation files are accessible:

- docs/00_PROJECT_STORY.md
- docs/01_CODING_RULES.md
- docs/02_SYSTEM_ARCHITECTURE.md
- docs/03_DATABASE_DESIGN.md
- docs/04_API_SPECIFICATION.md
- docs/05_ROADMAP.md
- docs/05_WORKFLOWS.md
- docs/06_CURRENT_TASK.md
- docs/07_DEVELOPMENT_GUIDELINES.md
- docs/08_AI_CONTEXT.md
- docs/09_COMPLETED_TASKS.md
- docs/10_NEXT_TASK.md
- docs/11_CHANGELOG.md
- docs/12_PROMPT_LIBRARY.md
- docs/13_DECISIONS.md

---

## Git State

The Git repository was freshly initialized after previous repository history was intentionally removed.

The primary branch is:

```text
master
```

The current repository should be treated as the source of truth.

Do not reset or recreate the repository.

---

## Development Rules

The AI must:

1. Read documentation.
2. Read current task.
3. Inspect code.
4. Implement only requested scope.
5. Test.
6. Validate.
7. Update documentation.
8. Report actual results.

---

## Hardware Context

Development machine:

- RTX 3060 12GB
- Intel i7-14700F
- 32GB RAM
- Windows

The user has experienced high RAM utilization when running local AI models. Model selection and agent runtime should consider resource usage.

---

## Next Step

STEP 23.2 — Vision Service & Model Router completed successfully:

- Vision Service connects to LM Studio ✓
- Model Router returns the Vision model ✓
- Vision Agent uses the Vision Service ✓
- Health checks succeed ✓
- Retry logic works ✓
- Configuration is externalized ✓
- Structured responses are returned ✓

*This context document reflects the current state of the AI agent system.*
