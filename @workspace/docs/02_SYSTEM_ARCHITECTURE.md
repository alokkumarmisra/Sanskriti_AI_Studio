# Sanskriti AI Studio — System Architecture

**Version:** 1.3  
**Status:** Active  
**Last Updated:** 2026-08-06

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

## 3. Frontend Architecture

Primary technologies:

- React
- TypeScript
- Vite
- TailwindCSS
- shadcn/ui
- TanStack Query

Typical flow:

```text
Page
 ↓
Component
 ↓
Hook / Query
 ↓
API Client
 ↓
FastAPI
```

TanStack Query manages server state, caching, loading and invalidation.

## 4. Backend Architecture

Recommended flow:

```text
HTTP Request
 ↓
FastAPI Router
 ↓
Pydantic Validation
 ↓
Service Layer
 ↓
Repository / Data Access
 ↓
SQLAlchemy
 ↓
PostgreSQL
```

Routers remain thin.

Services contain business logic.

Repositories handle persistence.

## 5. Database Architecture

PostgreSQL is the structured data source of truth.

The database may contain entities such as:

```text
Projects
Scenes
Prompts
Assets
Jobs
Metadata
```

Exact entities and relationships are defined in `03_DATABASE_DESIGN.md`.

Binary media should normally be stored outside PostgreSQL, with metadata and references stored in the database.

## 6. Project Architecture

A Project is the root organizational entity for a movie production.

Conceptually:

```text
Project
├── Scenes
├── Assets
├── Prompts
├── Jobs
└── Metadata
```

The exact relationships must follow the implemented database schema.

## 7. Frontend Project Flow

Current project workflow:

```text
/projects
    ↓
Projects List
    ↓
/projects/:projectId
    ↓
Project Detail
    ↓
Edit / Update / Delete
```

Project data must come from the backend API.

## 8. AI Architecture

AI services must be modular.

```text
Application
    ↓
AI Service Interface
    ↓
Provider Adapter
    ↓
Local AI Service
```

Examples:

```text
Text AI
 ↓
LM Studio Adapter
 ↓
Local LLM
```

```text
Visual Generation
 ↓
ComfyUI Adapter
 ↓
Image/Video Model
```

## 9. Qwen 3.5 Rule

Qwen 3.5 is TEXT-ONLY.

Allowed:

- Text
- Markdown
- JSON
- Code
- Logs
- Structured text

Not allowed:

- Images
- Screenshots
- Browser screenshots
- Image URLs
- Base64 images

Visual analysis must use a separate vision model.

## 10. Media Pipeline

Long-term workflow:

```text
Lyrics / Story
 ↓
Text Analysis
 ↓
Scene Breakdown
 ↓
Prompt Generation
 ↓
Image Generation
 ↓
Review
 ↓
Video Generation
 ↓
Review
 ↓
Upscaling
 ↓
Audio Synchronization
 ↓
FFmpeg Assembly
 ↓
Final Render
```

## 11. Job Architecture

Long-running operations should use jobs.

Examples:

- AI text generation
- Image generation
- Video generation
- Upscaling
- Rendering

Possible states:

```text
PENDING
QUEUED
RUNNING
COMPLETED
FAILED
CANCELLED
```

Only valid states in the current implementation may be used.

## 12. Agent Architecture

The development automation system may contain:

```text
Master Orchestrator
├── Planning Agent
├── Coding Agent
├── Testing Agent
├── Debugging Agent
├── Documentation Agent
├── Review Agent
├── Git Agent
└── Deployment Agent
```

Agents must have clear responsibilities and must report actual results.

## 13. Browser Verification

If browser output needs visual inspection:

```text
Browser
 ↓
Screenshot
 ↓
Vision-Capable Model
 ↓
Text / Structured Analysis
 ↓
Coding / Testing Agent
```

Never send the screenshot to Qwen 3.5.

## 14A. Vision Service & Model Router (STEP 23.2) — COMPLETED

The Vision Service and Model Router provide a centralized architecture for all vision model communication.

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

### Components

1. **Model Router** (`ai_agents/scripts/model_router.py`)
   - Centralized router for managing and selecting AI models
   - Provides `get_text_model()`, `get_vision_model()` methods
   - Implements `health_check()` with 60s caching
   - Supports `list_available_models()` for discovery
   - Request logging for audit trail

2. **Vision Service** (`ai_agents/scripts/vision_service.py`)
   - Handles ALL LM Studio vision communication
   - Implements retry logic with exponential backoff (default: 3 retries, 2x backoff)
   - Timeout handling per request (default: 300s)
   - Error classification and recovery
   - Health monitoring via `/models` endpoint
   - Image submission with base64 encoding

3. **Response Parser** (`ai_agents/scripts/response_parser.py`)
   - Normalizes Vision model responses into standardized format
   - Extracts: Summary, Components, OCR text, Issues, Warnings, Confidence, Suggested Fixes
   - Handles JSON and text-based responses
   - Extracts structured data from unstructured responses

4. **Vision Configuration** (`ai_agents/scripts/vision_config.py`)
   - Centralized configuration system
   - All values externalized via environment variables:
     - `LM_STUDIO_BASE_URL` (connection)
     - `CODING_MODEL` (text-only model, e.g., Qwen 3.5)
     - `VISION_MODEL` (vision model, e.g., Qwen2.5-VL)
     - `VISION_TIMEOUT`, `VISION_TEMPERATURE`, etc.
   - Configuration validation with error reporting

### Updated Vision Agent Flow

The Vision Agent (`ai_agents/scripts/vision_agent_new.py`) now follows:
- Gets model from Model Router (NOT hardcoded)
- Uses Vision Service for all LM Studio communication
- Logs all requests with request ID, duration, retry count
- Returns structured normalized responses

### Structured Response Format

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

### Health Monitoring

The Model Router implements automatic health checks:
- **LM Studio reachable** - Checks `/models` endpoint for availability
- **Vision model loaded** - Verifies vision model is available
- **Response time** - Measures latency with caching (60s expiry)
- **Connection status** - Maintains connection state, retries on temporary failures

## 14. Vision Agent Architecture (STEP 23.1) — COMPLETED

The Vision Agent provides independent visual analysis capabilities using a dedicated vision model (Qwen2.5-VL).

### Separation from Coding Agent

- **Coding Agent**: Generates source code, handles text-based reasoning
- **Vision Agent**: Analyzes UI screenshots, performs OCR, detects errors, validates layouts

They are separate agents with different models and responsibilities.

### Vision Model Integration

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

### Vision Agent Responsibilities

- Browser UI analysis from screenshots
- Screenshot understanding and description
- OCR text extraction
- Error message extraction
- Layout validation
- Visual regression testing
- UI element verification

### Structured Report Format (Legacy - STEP 23.1)

The Vision Agent returns structured JSON reports:

```json
{
  "status": "success | error",
  "task_type": "general|components|ocr|errors|layout|verify",
  "summary": "Brief summary of findings",
  "detected_components": [/* list of components */],
  "missing_components": [/* list if applicable */],
  "ocr_text": "/* extracted text */",
  "errors": [/* extracted errors */],
  "warnings": [/* warnings found */],
  "suggested_fixes": [/* recommendations */],
  "alignment_issues": [/* layout problems */]
}
```

### Model Configuration

The Vision Agent supports:

- **Vision Model Name**: Configurable via `LM_STUDIO_VISION_MODEL` env var
- **LM Studio Endpoint**: Configurable via `LM_STUDIO_BASE_URL` (default: `http://localhost:1234`)
- **Temperature**: Default 0.1 for deterministic outputs
- **Context Length**: Default 4096 tokens
- **Timeout**: 300 seconds for image processing

### Health Check

The vision endpoint supports health checks via `/models` endpoint to verify LM Studio availability and available models.

### Communication Bus Integration

The Vision Agent is registered with the communication bus at `ai_agents/communication_bus/vision.py`:

```python
VISION_AGENT_ID = "vision_agent"
VISION_AGENT_TYPE = "visual_analysis"
```

It supports message routing for vision-specific tasks and integrates with the existing agent communication infrastructure.

### Reviewer Integration

The Review Agent can consume Vision reports to merge:

1. **Code review findings** - from text/code analysis
2. **Visual review findings** - from Vision Agent reports  
3. **Validation results** - from test/build/lint stages

This provides comprehensive feedback for implementation quality.

## 15. Browser Automation Runtime (STEP 23.3) — COMPLETED

The Browser Automation Runtime provides a Playwright-based browser automation system that is independent from the Vision Agent.

### Architecture Flow (STEP 23.3)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Application │ →   │ Browser     │ →   │ Playwright  │ →   │ Chromium    │
│ /Agent      │     │ Runtime     │     │ API          │     │ Browser     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘

Key Principles:
1. Browser Runtime is independent from Vision Agent
2. All browser operations go through BrowserRuntime class
3. Configuration is externalized (no hardcoded values)
4. Error handling with retry logic
5. Page state collection for debugging
```

### Components

1. **Browser Configuration** (`ai_agents/scripts/browser_config.py`)
   - Centralized configuration system
   - All values externalized via environment variables:
     - `BROWSER_TYPE` (chromium/firefox/webkit)
     - `HEADLESS_MODE` (true/false)
     - `DEFAULT_TIMEOUT`, `NAVIGATION_TIMEOUT`
     - `VIEWPORT_WIDTH`, `VIEWPORT_HEIGHT`
     - `RETRY_COUNT`, `BACKOFF_FACTOR`
   - Configuration validation with error reporting

2. **Browser Runtime** (`ai_agents/scripts/browser_runtime.py`)
   - Manages browser lifecycle (launch/close)
   - Page navigation methods (goto, back, forward, refresh)
   - User interaction support (click, fill, type, select, check)
   - Page state collection (title, URL, console errors, network errors)
   - Error handling with retry policies

3. **Communication Bus Integration** (`ai_agents/communication_bus/browser.py`)
   - Registers Browser Runtime at `BROWSER_RUNTIME_ID = "browser_runtime"`
   - Exposes capabilities for Testing Agent and Reviewer Agent
   - Message routing for browser automation tasks

### Configuration Environment Variables

```bash
# Browser Type
export BROWSER_TYPE=chromium        # Options: chromium | firefox | webkit

# Execution Mode  
export HEADLESS_MODE=false          # false for visible, true for headless

# Timeout Settings (in seconds)
export DEFAULT_TIMEOUT=30           # Default operation timeout
export NAVIGATION_TIMEOUT=30        # Navigation timeout
export ELEMENT_TIMEOUT=5000         # Element interaction timeout (ms)

# Viewport Dimensions
export VIEWPORT_WIDTH=1280          # Viewport width in pixels
export VIEWPORT_HEIGHT=720          # Viewport height in pixels

# Retry Policy
export RETRY_COUNT=3                # Number of retries for operations
export BACKOFF_FACTOR=2.0           # Backoff multiplier for retries

# Color Scheme
export COLOR_SCHEME=dark            # Options: dark | light | auto

# Browser Arguments (optional)
export BROWSER_ARGS="--no-sandbox"  # Additional browser arguments
```

### Supported Operations

#### Lifecycle Operations (Phase 1)
- `launch()` - Launch Playwright browser
- `close()` - Close browser and all contexts
- `new_context(viewport, color_scheme)` - Create new context
- `is_launched` - Check if browser is launched

#### Navigation Operations (Phase 2)
- `goto(url)` - Navigate to URL
- `refresh()` - Reload current page
- `go_back()` - Navigate back in history
- `go_forward()` - Navigate forward in history
- `wait_for_load_state(state)` - Wait for load state (domcontentloaded/load/networkidle)
- `wait_for_network_idle()` - Wait for network to be idle
- `wait_for_element(selector)` - Wait for element to appear

#### User Interactions (Phase 3)
- `click(selector)` - Click on element
- `double_click(selector)` - Double click element
- `hover(selector)` - Hover over element
- `fill(selector, value)` - Fill input field
- `clear(selector)` - Clear input field
- `select(selector, option)` - Select dropdown option
- `check(selector)` - Check checkbox
- `type(selector, text)` - Type text into input
- `press_key(key)` - Press a key
- `scroll(direction, steps)` - Scroll page

#### Page State Collection (Phase 4)
- `get_title()` - Get page title
- `get_url()` - Get current URL
- `console_errors()` - Collect console errors
- `network_errors()` - Collect network errors
- `failed_requests()` - Get failed requests
- `load_time_ms()` - Get page load time

#### Error Handling (Phase 5)
- `handle_dialog(accept, prompt_text)` - Handle browser dialogs
- `with_retry(func, *args, **kwargs)` - Execute function with retry logic

### Usage Example

```python
from ai_agents.scripts.browser_runtime import BrowserRuntime
from ai_agents.scripts.browser_config import get_browser_config

async def example_usage():
    # Get configuration from environment
    config = get_browser_config()
    
    # Create browser runtime
    runtime = BrowserRuntime(config)
    
    # Launch browser
    await runtime.launch()
    
    # Navigate to a page
    current_url = await runtime.goto("https://example.com")
    
    # Perform interactions
    await runtime.click("#header")
    await runtime.fill("#search", "query text")
    await runtime.press_key("Enter")
    
    # Collect page state
    title = await runtime.get_title()
    console_errors = await runtime.console_errors()
    
    # Close browser
    await runtime.close()

# Or use the Communication Bus for messaging
from ai_agents.communication_bus.browser import build_browser_message, execute_browser_action

message = build_browser_message(
    action="navigate",
    url="https://example.com",
)

response = await execute_browser_action(message)
```

### Future Consumers

The Browser Runtime is exposed through the Communication Bus for:
- **Testing Agent** - Automated browser testing and regression testing
- **Reviewer Agent** - UI verification and layout validation
- **Other automation tasks** - Any agent requiring browser interaction

### Qwen 3.5 Rule Compliance

The Browser Runtime itself is text-only. Screenshot capture is provided separately for the Vision Agent to analyze:

```text
BrowserRuntime → Screenshot Capture → Vision-Capable Model (Qwen2.5-VL)
                                              ↓
                                    Structured Analysis Report
```

## 16. Local-First Architecture

The target environment is:

```text
Windows PC
├── Sanskriti AI Studio
├── PostgreSQL
├── LM Studio
├── ComfyUI
├── Local Models
└── FFmpeg
```

## 17. Current Milestones

Completed:

- 6.1 Database Foundation
- 6.2 Projects Backend APIs
- 6.3 Projects Frontend UI
- 6.4 Seed Data and API Verification
- 6.5 Project Detail and Project Management UI
- **STEP 23.1 — Vision Agent** (Vision Agent Runtime, ai_agents/scripts/vision_agent_new.py)
- **STEP 23.2 — Vision Service & Model Router** (vision_service.py, model_router.py)
- **STEP 23.3 — Browser Automation Runtime** (browser_runtime.py, browser_config.py)

The next milestone is determined by `10_NEXT_TASK.md`.
