# Sanskriti AI Studio — System Architecture

**Version:** 1.5  
**Status:** Active  
**Last Updated:** 2026-08-07 (STEP 23.9)

## 1. Purpose

This document defines the technical architecture of Sanskriti AI Studio.

It covers:

- Frontend
- Backend
- Database
- AI services
- Media processing
- Background jobs
- File storage
- AI agents
- Local development
- Vision Analysis Pipeline (STEP 23.5)
- UI Validation Engine (STEP 23.6)
- Self-Healing Development Loop (STEP 23.8)
- **Human Approval Dashboard (STEP 23.9)**

Significant architectural changes must be recorded in `docs/13_DECISIONS.md`.

## 2. High-Level Architecture

```text
React + TypeScript Frontend
         ↓ HTTP/REST
FastAPI Backend
         ↓
Services
         ↓
Repositories / Data Access
         ↓
PostgreSQL
```

AI and media services are accessed through integration layers:

```text
Application
    ↓
AI / Media Service
    ↓
Adapter / Client
    ↓
LM Studio / ComfyUI / FFmpeg
```

## 3. AI Agents Architecture

The AI agents layer provides intelligent automation capabilities with a strict separation between text-only and vision-capable models.

### 3.1 Qwen 3.5 (Text-Only)

Qwen 3.5 is strictly TEXT-ONLY. It must never receive image inputs, screenshots, or visual data.

Usage:
- Text analysis
- Code review
- Documentation generation
- Debugging assistance
- Project planning
- Code completion

### 3.2 Vision Agents (Image-Capable)

Vision agents use vision-capable models (Qwen2.5-VL) for image-based analysis tasks.

Usage:
- UI screenshot analysis
- Component detection
- OCR text extraction
- Error message detection
- Layout analysis
- Visual regression testing

### 3.3 Communication Bus

The Communication Bus manages messaging between agents:
- Message routing based on destination agent
- Duplicate detection
- Request/response tracking
- Priority handling
- Broadcast capabilities

## 4. Vision Analysis Pipeline (STEP 23.5)

The Vision Analysis Pipeline provides end-to-end automated visual analysis using the local Qwen2.5-VL model.

### 4.1 Architecture

```text
Browser Runtime → Screenshot Service → Vision Agent → Vision Service → Model Router → LM Studio (Qwen2.5-VL)
     ↓              ↓                    ↓                  ↓                 ↓
  Navigation    Capture & Store      Analysis           Request Format   Model Selection
```

### 4.2 Execution Flow (Phase 2)

The pipeline follows this exact execution sequence:

1. **Browser Runtime** - Launch browser and navigate to target URL
2. **Screenshot Service** - Capture and store screenshot with metadata
3. **Vision Agent** - Prepare analysis request with appropriate prompt
4. **Vision Service** - Interface with LM Studio, handle requests
5. **Model Router** - Select Qwen2.5-VL model for vision tasks
6. **LM Studio** - Execute model inference (Qwen2.5-VL-8B)

### 4.3 Pipeline Orchestrator (Phase 1)

The `VisionPipeline` orchestrator is responsible for:
- Receiving analysis requests
- Coordinating execution flow
- Handling retries with exponential backoff
- Tracking execution status
- Collecting results
- Publishing lifecycle events
- Storing execution history

### 4.4 Standard Response Schema (Phase 3)

The pipeline produces structured `VisionAnalysisReport` objects containing:

| Field | Type | Description |
|-------|------|-------------|
| analysis_id | string | Unique identifier for this analysis |
| session_id | string | Session context identifier |
| screenshot_id | string | Screenshot reference identifier |
| url | string | Page URL analyzed |
| page_title | string | Extracted page title |
| summary | string | Overall analysis summary |
| detected_components | array | List of detected UI components |
| missing_components | array | Expected but absent components |
| ocr_text | string | Extracted text content |
| visual_issues | array | Layout/rendering issues found |
| warnings | array | Non-critical findings |
| suggested_improvements | array | Recommendations for improvement |
| confidence_score | float | Quality score (0-100) |
| processing_time_ms | float | Duration in milliseconds |

### 4.5 Lifecycle Events (Phase 4)

The pipeline publishes the following events:

1. **Analysis Started** - Pipeline initiated with request details
2. **Screenshot Captured** - Image captured and stored with metadata
3. **Vision Request Sent** - Request forwarded to Vision Service
4. **Vision Response Received** - Model response received from LM Studio
5. **Analysis Completed** - Success with structured report
6. **Analysis Failed** - Error with diagnostics

### 4.6 Error Recovery (Phase 5)

The pipeline implements robust error recovery:

| Error Type | Recovery Strategy |
|------------|-------------------|
| Screenshot missing | Retry capture (max 2 retries) or mark as error |
| Vision timeout | Wait exponential backoff, retry up to max_retries |
| LM Studio unavailable | Health check → wait → retry; fail gracefully if persistent |
| Invalid response format | Fallback to text extraction or return error schema |
| Corrupt image | Skip analysis, generate error report with diagnostics |

### 4.7 Execution History (Phase 7)

Analysis history is stored in `ai_agents/state/vision_history.jsonl` containing:
- Analysis ID
- Screenshot path reference
- Report summary
- Timestamps (start, end)
- Duration
- Status (success/failed)
- Error messages (if applicable)

### 4.8 Reviewer Integration (Phase 6)

The structured `VisionAnalysisReport` returned by the pipeline can be:
1. Attached to project review data structures
2. Sent via Communication Bus to Reviewer Agent
3. Stored alongside other analysis results for historical comparison

## 5. UI Validation Engine (STEP 23.6)

The UI Validation Engine compares Vision Analysis results against expected UI definitions to determine whether the user interface satisfies milestone acceptance criteria.

### 5.1 Architecture

```text
Vision Analysis Report
        ↓
   Comparison Engine
        ↓
UI Validation Engine
        ↓
Validation Report + History
        ↓
    Reviewer Agent
```

### 5.2 Components

- **Validation Rules** (`ai_agents/scripts/validation_rules.py`) - Defines all validation categories and rule definitions
- **Expected UI Model** (`validation_rules.py:ExpectedUIModel`) - Reusable UI expectation definitions for each page
- **Comparison Engine** (`ai_agents/scripts/comparison_engine.py`) - Compares expected vs actual UI
- **Validation Report Schema** (`ai_agents/scripts/validation_engine.py:ValidationReport`) - Structured validation results
- **Validation History Manager** (`ai_agents/scripts/validation_history.py`) - Stores and analyzes validation history
- **UI Validation Engine** (`ai_agents/scripts/validation_engine.py:UIValidationEngine`) - Main orchestration class

### 5.3 Comparison Strategy (Phase 4)

The comparison engine identifies:
- Missing Components - Expected but not found
- Unexpected Components - Found but not expected
- Incorrect Labels - Text mismatches on interactive elements
- Layout Problems - Structural issues from visual analysis
- Accessibility Warnings - Missing ARIA labels, etc.
- Navigation Problems - Broken links, missing nav elements

### 5.4 Validation Report Schema (Phase 5)

| Field | Type | Description |
|-------|------|-------------|
| validation_id | string | Unique identifier for this validation run |
| milestone_id | string | Milestone being validated |
| task_id | string | Task identifier within the milestone |
| page_name | string | Page name from expected UI model |
| status | string | PASS or FAIL |
| score | float | Validation score (0-100) |
| satisfied_rules | array | Rules that passed validation |
| failed_rules | array | Rules that failed validation |
| warnings | array | Warnings detected (INFO level) |
| recommendations | array | Actionable recommendations |

### 5.5 Reviewer Integration (Phase 6)

The Reviewer Agent now merges:
1. Code Review findings
2. Test Results
3. Vision Analysis (STEP 23.5)
4. UI Validation (STEP 23.6)

A single review summary is generated that considers all sources.

### 5.6 Validation History (Phase 7)

History supports:
- Pass Rate calculation
- Failure Rate calculation
- Historical Reports retrieval
- Trend Analysis (improving/degrading/stable)

## 6. Self-Healing Development Loop (STEP 23.8)

The Self-Healing Development Loop provides an autonomous execution loop that continuously attempts to fix implementation issues until the project passes all validation or reaches a configurable retry limit.

### 6.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LOOP CONTROLLER                           │
│              (ai_agents/scripts/self_healing_loop.py)        │
└─────────────────────────────────────────────────────────────┘
                              ↓
         ┌───────────────────────────────────────────────────────┐
         │                   INITIAL WORKFLOW                     │
         │   Planner → Coding → Testing → Vision → UI Validation  │
         │   → Screenshot → Browser Runtime                       │
         └───────────────────────────────────────────────────────┘
                              ↓
                  ┌────────────────────────┐
                  │     REVIEWER AGENT      │
                  │    (PASS/FAIL)          │
                  └────────────────────────┘
                         ↓
           ┌─────────────┴─────────────┐
           ↓                           ↓
    [PASS] → Documentation Agent → Complete
           ↓                           ↓
     [FAIL + Retries Remaining]     [Retry Limit Reached / Critical Fail]
           ↓                           ↓
    ┌──────────────────────────────────┘
    │
    ↓
   DEBUGGING AGENT → CODING AGENT → TESTING AGENT → Reviewer Agent
   (Analyze)      (Apply Fix)      (Validate)         (Re-evaluate)
```

### 6.2 Loop Controller Responsibilities

The `LoopController` class in `ai_agents/scripts/self_healing_loop.py` handles:

- **Start Execution** - Initiates the loop with execution ID generation
- **Monitor Execution State** - Tracks current stage and agent status
- **Track Retry Count** - Maintains retry counter per execution
- **Stop on Success** - Terminates when Reviewer returns PASS
- **Stop on Retry Limit** - Terminates after configurable max retries
- **Persist Execution State** - Stores state in `ai_agents/state/loop/`

### 6.3 Loop Flow (Phase 2)

The workflow follows this sequence:

1. **Planner Agent** → Task planning and task plan creation
2. **Coding Agent** → Code implementation/reasoning
3. **Build Project** → Build validation
4. **Testing Agent** → Unit test execution
5. **Browser Runtime** → Browser automation setup
6. **Screenshot Service** → Visual capture
7. **Vision Agent** → Visual analysis request preparation
8. **Vision Analysis** → Qwen2.5-VL model inference via LM Studio
9. **UI Validation Engine** → Compare actual vs expected UI
10. **Reviewer Agent** → Final PASS/NEEDS_CHANGES/FAIL decision

If REVIEWER returns PASS:
- Documentation Agent generates completion docs
- Loop terminates successfully

If REVIEWER returns FAIL and retries remain:
- Debugging Agent analyzes failure
- Coding Agent applies fix
- Testing Agent validates
- Repeat through Reviewer

### 6.4 Retry Policy (Phase 3)

The controller supports configurable retry limits:

| Parameter | Default | Configurable Via |
|-----------|---------|------------------|
| Maximum Retry Count | 5 | `--retries N` or state config |
| Retry Delay | 30s | `--delay N` or state config |
| Critical Failure Stop | Yes | Config option |

**Exponential Backoff**: Delay = base_delay × 2^(retry_count - 1)

### 6.5 Failure Analysis (Phase 4)

The controller tracks and categorizes failures:

- **Compilation Errors** - Syntax/compilation failures
- **Test Failures** - Assertion/test assertion failures  
- **Browser Failures** - Browser automation errors
- **Vision Failures** - Vision pipeline/model timeout errors
- **Validation Failures** - UI validation rule failures
- **Runtime Exceptions** - Unexpected exceptions

Severity categorization:
- **CRITICAL**: Application crash, browser crash, compilation error
- **HIGH**: Test failures, validation failures, runtime exceptions
- **MEDIUM**: Unknown errors

### 6.6 Loop History (Phase 5)

Execution history is stored in `ai_agents/state/loop/` containing:

- `loop_status.json` - Current execution state
- `current_execution_id.txt` - Execution ID
- `actions.jsonl` - All agent actions logged
- Individual agent output files

History includes:
- **Execution ID** - Unique identifier for this loop run
- **Retry Count** - Number of retry attempts made
- **Current Stage** - Last executed workflow stage
- **Current Agent** - Last active agent
- **Failure History** - List of all failures with details
- **Applied Fixes** - Code changes applied during retries
- **Duration** - Total execution time in milliseconds
- **Final Status** - PASS/RETRY_LIMIT_REACHED/FAILURE

### 6.7 Recovery Strategy (Phase 6)

The controller supports recovery after:

- **Application Crash** - Restart from last stable state
- **Browser Crash** - Re-initialize browser runtime
- **LM Studio Timeout** - Retry with backoff, check health
- **Vision Timeout** - Retry vision analysis with backoff
- **Unexpected Exceptions** - Catch and log, retry if non-critical

Recovery preserves:
- Execution ID continuity
- Failure history for analysis
- Partial results where possible

### 6.8 Reviewer Integration (Phase 7)

The loop only finishes when:
- **Reviewer returns PASS** → Documentation generated, complete
- **Retry limit reached** → Terminate with RETRY_LIMIT_REACHED status

### 6.9 Execution State Schema

```json
{
  "execution_id": "LOOP-20260807104000-abcd1234",
  "task_id": "loop-init",
  "retry_count": 3,
  "current_stage": "reviewer_agent",
  "current_agent": "Reviewer Agent",
  "failure_history": [
    {"stage": "Coding Agent", "status": "failed", "error": "...", "timestamp": "..."}
  ],
  "applied_fixes": [],
  "start_time": "2026-08-07T10:40:00.000Z",
  "end_time": "2026-08-07T10:55:00.000Z",
  "status": "RUNNING|COMPLETED|TERMINATED|STOPPED",
  "final_status": "PASS|RETRY_LIMIT_REACHED|FAILURE",
  "duration_ms": 900000,
  "stop_reason": null
}
```

## 7. Human Approval Dashboard (STEP 23.9)

The Human Approval Dashboard provides a centralized interface for human reviewers to monitor, inspect, approve, reject, or re-run AI-generated work before it is finalized.

### 7.1 Architecture

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   State     │ →   │  Dashboard  │ →   │   Frontend  │
│  Files      │     │   CLI       │     │   UI        │
└─────────────┘     └─────────────┘     └─────────────┘

Key Principles:
1. Reuses existing agent data - no duplicate reporting systems
2. Reads from shared state files
3. Provides structured aggregation for frontend consumption
4. Supports manual approval workflow
5. Qwen 3.5 TEXT-ONLY compliance
```

### 7.2 Components

The dashboard aggregates data from:
- **Coding Agent** (via coding_result.json/actions.jsonl)
- **Testing Agent** (via test_report.json)
- **Reviewer Agent** (via review_report.json)
- **Validation Engine** (via validation_history.json)
- **Vision Agent** (via vision_report.json if available)

### 7.3 Dashboard Phases

| Phase | Description | Data Source |
|-------|-------------|-------------|
| 1 | Current Execution Status | task_plan/current_task/actions.jsonl |
| 2 | Build Status | test_report.json (backend tests) |
| 3 | Test Results | test_report.json (unit/integration tests) |
| 4 | Vision Results | vision_report.json (if available) |
| 5 | UI Validation | validation_history.json |
| 6 | Review Report | review_report.json |
| 7 | User Actions | Built-in approval workflow |
| 8 | History | actions.jsonl (execution history) |
| 9 | Documentation | docs/ timestamp tracking |

### 7.4 User Actions (Phase 7)

The dashboard provides the following user actions:

1. **Approve** - Accept completed work and proceed to next milestone
2. **Reject** - Reject current work, return for fixes
3. **Re-run Current Step** - Rerun specific agent stage
4. **Restart Self-Healing Loop** - Reset autonomous development loop
5. **Continue to Next Milestone** - Skip to next milestone after approval
6. **Export Report** - Generate JSON report of current state
7. **View History** - Access execution timeline and previous runs

### 7.5 Qwen 3.5 Compliance

The dashboard adheres to Qwen 3.5 TEXT-ONLY requirements:
- Never sends images to any models
- Only uses text-based data aggregation
- All analysis is performed on structured JSON/text data

## 8. Completed Milestones

- STEP 23.1 — Vision Agent Runtime ✓
- STEP 23.2 — Vision Service & Model Router ✓
- STEP 23.3 — Browser Automation Runtime ✓
- STEP 23.4 — Screenshot Capture Service ✓
- STEP 23.5 — Vision Analysis Pipeline ✓
- STEP 23.6 — UI Validation Engine ✓
- STEP 23.7 — Autonomous Visual Reviewer ✓
- STEP 23.8 — Self-Healing Development Loop ✓
- **STEP 23.9 — Human Approval Dashboard** ✓

## 9. Next Steps

The next milestone is determined by `docs/10_NEXT_TASK.md`.
