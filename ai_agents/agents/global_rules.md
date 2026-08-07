# Global Rules for Sanskriti AI Studio Multi-Agent System

## Introduction

These rules are permanent and must be followed by every AI agent operating within the Sanskriti AI Studio multi-agent system. They ensure consistency, safety, and reliability across all agent operations.

Every agent must read and internalize these rules before executing any task.

---

## 1. Documentation-First Development

**Rule**: All development begins with reading relevant documentation.

### Required Reading Order:
1. `docs/01_AGENTS.md` - Core development rules
2. `docs/02_ARCHITECTURE.md` - System architecture and layer responsibilities
3. `ai_agents/README.md` - Workspace-specific guidance
4. Task-specific documentation before implementation

### Enforcement:
- Never implement a feature without reading the architecture document first
- Always verify existing implementations before creating new code
- Refer to roadmap only for milestone planning, not execution

---

## 2. Read Current Task Before Implementation

**Rule**: Understand the complete task before writing any code.

### Required Steps:
1. Read the full task description
2. Identify all requirements and constraints
3. Determine which documentation files are relevant
4. Confirm understanding of success criteria
5. Ask clarifying questions if anything is unclear

### Prohibited:
- Do not skip to implementation without understanding the full scope
- Do not assume requirements that aren't stated
- Do not start coding before reading all relevant files

---

## 3. Inspect Existing Code Before Creating New Code

**Rule**: Never create code until you understand what already exists.

### Inspection Checklist:
- [ ] Read existing similar implementations
- [ ] Understand current API contracts
- [ ] Review database schema (if applicable)
- [ ] Check service interfaces and dependencies
- [ ] Identify reusable utilities and helpers
- [ ] Verify no duplicate functionality exists

### Enforcement:
- If a similar component exists, reuse it instead of creating a duplicate
- Document what you found in your inspection
- Report any gaps or inconsistencies discovered

---

## 4. Reuse Existing Architecture

**Rule**: The established architecture must not be modified for simple features.

### Layer Responsibilities (Must Not Be Bypassed):
```
User → Frontend (UI only) → API (requests/responses) 
     → Services (business logic) → Repositories (database access)
     → Database | AI Services (external calls)
```

### Enforcement:
- Never let frontend access database directly
- Never let services communicate with UI
- Never bypass layers with direct file system access for core features
- Use existing service interfaces, not internal implementations

---

## 5. Avoid Duplicate Functionality

**Rule**: Do not create code that already exists elsewhere.

### Before Creating Anything:
1. Search existing codebase for similar functionality
2. Check if the feature is part of an existing module
3. Verify the use case isn't already covered
4. Document any gaps found

### Prohibited Patterns:
- Duplicate service implementations
- Redundant API endpoints
- Multiple ways to accomplish the same task
- Repeated prompts for similar queries

---

## 6. Preserve Working Functionality

**Rule**: Never break existing functionality while implementing new features.

### Safety Checklist:
- [ ] Verify all tests pass after changes
- [ ] Run lint checks before committing
- [ ] Test build pipeline succeeds
- [ ] Check API endpoints still respond correctly
- [ ] Confirm database schema is unchanged (unless intended)
- [ ] Verify no unintended side effects

### If Something Breaks:
1. Identify the root cause immediately
2. Do not continue with other tasks until fixed
3. Report the issue with clear diagnosis
4. Implement a fix before proceeding

---

## 7. Implement Only Assigned Task

**Rule**: Execute only what is explicitly requested.

### Scope Discipline:
- Implement the specific feature described in the task
- Do not add "improvements" that weren't requested
- Do not implement future features or enhancements
- Keep changes minimal and focused

### Example:
```
Task: Add user authentication
DO: Implement JWT-based auth with login/logout
DON'T: Add social auth, password reset, 2FA without being asked
```

---

## 8. Never Implement Future Milestones Automatically

**Rule**: Do not implement upcoming roadmap items without explicit instruction.

### Roadmap Discipline:
- Read `docs/06_ROADMAP.md` to understand planned features
- Do NOT implement Phase 1 before Phase 0 is complete
- Do NOT skip to future milestones unless explicitly instructed
- Report when a feature appears ready but not yet requested

---

## 9. Git Safety

**Rule**: Protect the Git repository from accidental damage.

### Prohibited Operations:
- NEVER switch branches
- NEVER merge master/main into current branch
- NEVER reset HEAD or modify Git history
- NEVER force push
- NEVER delete branches
- NEVER amend previous commits
- NEVER modify `.git/config`

### Allowed Operations:
- Commit new files to `ai_agents/` directory
- Commit changes to existing files when explicitly instructed
- Create pull requests for review
- Use Git commands ONLY when explicitly requested

### Git Bash Preference:
Use Git Bash for all Git operations to ensure consistent behavior.

```bash
# Preferred syntax (Git Bash)
git add .
git commit -m "Message"
git push origin <branch>
```

---

## 10. Testing Requirements

**Rule**: All code changes must be tested before reporting completion.

### Backend Testing:
```bash
cd backend
python -m pytest
# or run specific test file if applicable
```

### Frontend Testing:
```bash
cd frontend
npm run test
npm run lint
npm run build
```

### Verification Checklist:
- [ ] Unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] Linting passes with no errors or warnings
- [ ] Build succeeds without errors
- [ ] Manual API verification via Swagger/Postman
- [ ] Frontend functionality verified in browser

### Error Diagnosis:
If tests fail:
1. Read the full error message carefully
2. Identify the root cause (not just symptoms)
3. Check if it's a known issue or new problem
4. Fix only what causes the test failure
5. Do not report PASS until all tests pass

---

## 11. Build and Lint Requirements

**Rule**: Code must meet quality standards before completion.

### Build Commands:
```bash
# Backend - verify Python environment
cd backend
pip install -r requirements.txt  # or uv sync
python -c "import app"  # verify imports work

# Frontend - verify build pipeline
cd frontend
npm run lint
npm run build
```

### Lint Checklist:
- [ ] No ESLint errors (frontend)
- [ ] No Pylint/flake8 issues (backend)
- [ ] Type annotations complete (TypeScript/Python)
- [ ] No console.log() in production code
- [ ] No TODO comments without action items

### Linting Result Reporting:
Always report:
```
Lint result: PASS / FAIL
```

If lint fails, fix all issues before marking complete.

---

## 12. Error Diagnosis Protocol

**Rule**: When errors occur, diagnose thoroughly before retrying.

### Diagnostic Steps:
1. **Read the full error message** - Don't scroll past it
2. **Identify error type** - Syntax, runtime, import, etc.
3. **Check context** - What was being executed?
4. **Verify dependencies** - Are packages installed/available?
5. **Review recent changes** - What caused this?
6. **Search for similar errors** - Has this happened before?

### Common Mistakes to Avoid:
- Running the same failing command 10 times without analysis
- Ignoring error messages and guessing fixes
- Making unrelated code changes to "fix" something else
- Overwriting files with incorrect data

### If Command Fails:
```
DO: Analyze the error, identify root cause, fix specifically that issue
DON'T: Run the same command repeatedly without fixing anything first
DON'T: Assume it will work after a retry
```

---

## 13. Documentation Updates

**Rule**: Update documentation when implementation changes requirements.

### When to Update Docs:
- API contracts change (update schema docs)
- New features added to roadmap
- Architecture decisions made
- Database schema modified
- Agent capabilities evolve

### Documentation Checklist:
```
After implementation, check if these need updates:
- [ ] API specification docs
- [ ] Architecture documentation
- [ ] Roadmap status
- [ ] This global rules document (if needed)
- [ ] Any README files affected by changes
```

---

## 14. Agent Communication Format

**Rule**: All agents communicate using structured, documented formats.

### Communication Channels:

#### Shared State Store (`ai_agents/state/`)
- JSON-based state files
- Each agent uses namespaced keys
- Read-write memory for collaboration
- Example format:
```json
{
  "agent_id": "project_manager",
  "task": "create_project",
  "status": "pending|processing|complete",
  "data": {
    "project_name": "example",
    "config": {}
  },
  "timestamp": "2026-07-29T12:00:00Z"
}
```

#### Event Logs (`ai_agents/logs/events/`)
- Async event publication/subscription
- Structured log entries
- Example format:
```json
{
  "event_type": "task_started|task_completed|error|completed",
  "agent_id": "planner",
  "payload": {"details..."},
  "timestamp": "2026-07-29T12:00:00Z"
}
```

#### Message Queue (`ai_agents/scripts/`)
- Script-based task processing
- Reliability through persistence
- Example scripts:
  - `orchestrate.py` - Main orchestration logic
  - `monitor.py` - Health and status checks

### Inter-Agent Protocol:
```
User Request → Planner Agent 
     ↓ Task Breakdown & State Update
Executor Agents (parallel or sequential)
     ↓ Results written to State
Review Agent (Quality Check)
     ↓ Final State Update
Final Output delivered
```

---

## 15. Task Status Reporting

**Rule**: Always report completion status with full details.

### Required Report Format:

```
Files Created:
- List all new files with paths

Files Modified:
- List all modified files with paths

Files Deleted:
- List all deleted files (if any)

Tests Executed:
- Command used and results

Build Result:
- PASS / FAIL

Lint Result:
- PASS / FAIL

API Verification:
- Status and notes

Database Verification:
- Schema unchanged or migration applied

Frontend Verification:
- Browser test status

Known Issues:
- Any warnings or incomplete items

Remaining Work:
- Next steps if applicable
```

### Qwen 3.5 Text-Only Check (Required):
```
TEXT-ONLY LLM CHECK:
- Images sent to Qwen 3.5: NO
- Image input added: NO
- Visual analysis attempted: NO
```

---

## CRITICAL RULE: Qwen 3.5 is TEXT-ONLY

### Rule Statement:
**Qwen 3.5 is a TEXT-ONLY Large Language Model.**

It must NEVER receive or process images, visual data, or any form of image input.

### Prohibited Inputs:
NEVER send to Qwen 3.5:
- Images
- Screenshots
- Image files (PNG, JPG, GIF, SVG, etc.)
- Image URLs
- Browser screenshots
- Base64-encoded images
- Visual content of any kind

### Correct Workflow for Visual Analysis:

If a task requires visual analysis:

```
Visual Task Detected → Vision Model (if available) → 
    ↓ Text Description Generated
Text-Only Diagnosis → Qwen 3.5
    ↓ Final Report
Output to User
```

### Example Scenarios:

#### ❌ WRONG: Sending screenshot to Qwen 3.5
```
User: "Here's a screenshot of the error"
→ [ATTACHES IMAGE]
Qwen 3.5: Processes image (TEXT-ONLY VIOLATION)
```

#### ✅ CORRECT: Using Vision Model first
```
User: "There's an error in the application"
Vision Model: Analyzes visual elements → "Error occurs at button click, stack shows TypeError"
→ Generates text description
Qwen 3.5: Processes text description → Provides solution
```

### Enforcement:
- If visual input is required, route through Vision Model first
- Convert visual output to text before sending to Qwen 3.5
- Report any visual analysis requirements as "NEEDS VISION MODEL"
- Never assume Qwen 3.5 can handle images

---

## 16. Isolation from Frontend/Backend Code

**Rule**: The AI agent workspace must not modify core application code.

### Protected Directories:
```
DO NOT MODIFY:
├── frontend/           (React application)
├── backend/            (FastAPI application)
├── database/           (Database schema/migrations)
└── Git history         (Git repository integrity)
```

### Allowed Modifications:
Only within `ai_agents/`:
```
ai_agents/
├── agents/              (Agent implementations)
├── prompts/             (Prompt templates)
├── state/               (Agent state files)
├── logs/                (Agent operation logs)
└── scripts/             (Orchestration utilities)
```

### Communication Boundaries:
- Agents read/write to `ai_agents/state/` only
- No direct database access from agents
- No direct API calls except through defined services
- All agent coordination through shared state and events

---

## Quick Reference Checklist

Before implementing any feature:

### Documentation Reading:
```
☐ Read docs/01_AGENTS.md
☐ Read docs/02_ARCHITECTURE.md
☐ Read ai_agents/README.md
☐ Review relevant task documentation
```

### Code Inspection:
```
☐ Inspect existing implementations
☐ Verify no duplicate functionality exists
☐ Understand current architecture constraints
☐ Identify reusable components
```

### Implementation Rules:
```
☐ Implement only the assigned task
☐ Never implement future milestones
☐ Reuse existing code and patterns
☐ Preserve working functionality
```

### Safety Rules:
```
☐ Never modify Git history
☐ Never switch branches
☐ Never force push or reset
☐ Only work within ai_agents/ directory (for new features)
☐ Qwen 3.5 receives text only (never images)
```

### Validation Checklist:
```
☐ Run backend tests
☐ Run frontend tests
☐ Run npm lint
☐ Run npm build
☐ Verify API endpoints
☐ Check database schema unchanged
☐ Manual verification where applicable
```

### Reporting Requirements:
```
☐ Files created/modified/deleted listed
☐ Tests results included
☐ Build result stated
☐ Lint result stated
☐ Any issues reported
☐ TEXT-ONLY CHECK completed (no images sent)
```

---

## Conclusion

These global rules form the foundation of safe, reliable development within Sanskriti AI Studio. Every agent must:

1. **Read** all relevant documentation before acting
2. **Inspect** existing code and architecture
3. **Implement** only what is requested
4. **Validate** all changes thoroughly
5. **Report** with complete details
6. **Protect** core application and Git integrity

Violating these rules compromises system stability, data integrity, or project safety.

---

*Last Updated: 2026-07-29*  
*Version: 1.0 - Permanent Global Rules*
