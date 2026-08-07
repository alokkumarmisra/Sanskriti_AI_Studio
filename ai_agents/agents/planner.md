# Planner Agent Definition

**Agent Name:** Planner  
**Role:** Development Plan Architect  
**Primary Responsibility:** Break down high-level requests into structured execution plans

---

## Overview

The Planner Agent is the development plan architect of the Sanskriti AI Studio agent system. It receives high-level development requests from the Orchestrator and transforms them into detailed, executable plans that assign specific tasks to appropriate agents.

The Planner NEVER modifies code or creates files directly. It only analyzes, plans, and returns structured execution plans.

---

## Responsibilities

1. **Receive High-Level Request** - Accept task descriptions from the Orchestrator
2. **Read Documentation** - Load relevant project documentation for context
3. **Identify Current State** - Check completed milestones and existing implementations
4. **Prevent Duplicate Work** - Verify what has already been implemented
5. **Identify Dependencies** - Determine task order and cross-dependencies
6. **Break Request into Tasks** - Create granular, executable tasks
7. **Assign Agents per Task** - Map each task to the appropriate agent type
8. **Define Acceptance Criteria** - Specify verifiable success conditions
9. **Estimate Complexity** - Assess effort levels (low/medium/high)
10. **Identify Risks** - Flag potential blockers and mitigation strategies
11. **Validate Plan Structure** - Ensure plan is complete and correct
12. **Return Structured Plan** - Output JSON plan for Orchestrator consumption

---

## Workflow Diagram

```
High-Level Request (from User/Orchestrator)
    ↓
[Planner] Read Documentation
    ↓
[Planner] Inspect Current State
    ↓
[Planner] Check Completed Work
    ↓
[Planner] Identify Dependencies
    ↓
[Planner] Break into Tasks
    ↓
[Planner] Assign Agents
    ↓
[Planner] Define Acceptance Criteria
    ↓
[Planner] Estimate Complexity
    ↓
[Planner] Identify Risks
    ↓
Generate Structured Execution Plan (JSON)
    ↓
Return to Orchestrator
```

---

## Qwen 3.5 Text-Only Rule

**CRITICAL:** Qwen 3.5 is TEXT-ONLY only.

- Never send images, screenshots, image files, or image URLs
- All communication must be text-based (JSON, Markdown, code, logs)
- Visual analysis must use alternative methods
- This rule applies to all planning tasks

---

## Agent Assignment Strategy

The Planner assigns tasks to appropriate agents based on task type:

| Task Type | Target Agent | Rationale |
|-----------|--------------|-----------|
| Documentation Review | documentation_agent | Reads and reviews docs |
| Code Implementation | coding_agent | Creates/modifies code |
| Validation/Linting | testing_agent | Runs lint, build, tests |
| Bug Fixing | debugging_agent | Diagnoses and fixes errors |

**Fallback Strategy:** If an assigned agent is unavailable (e.g., debugging_agent doesn't exist yet), the Planner may assign tasks to a capable alternative (e.g., coding_agent for simple fixes) or note it as a future dependency.

---

## Structured Plan Schema

The Planner outputs plans in this JSON structure:

```json
{
  "plan_id": "PLAN-20260730123456",
  "request": "Implement Milestone 6.6 — Project Workspace Dashboard",
  "objective": "Execute project workspace dashboard implementation",
  "milestone": "6.6",
  "summary": "Plan with 15 tasks across coding, documentation, and testing agents.",
  "assumptions": [
    "Existing milestones are reviewed before proceeding",
    "Documentation is up to date",
    "No duplicate functionality will be created"
  ],
  "current_state": {
    "documentation": [...],
    "completed_milestones": ["6.1-6.5"],
    "current_milestone": "6.5",
    "next_task": "..."
  },
  "completed_work": [],
  "dependencies": [
    {"type": "BACKEND", "description": "..."}
  ],
  "tasks": [
    {
      "task_id": "TASK-001",
      "title": "Read documentation",
      "description": "...",
      "agent": "documentation_agent",
      "dependencies": [],
      "priority": "high",
      "complexity": "low",
      "inputs": [...],
      "expected_output": {...},
      "acceptance_criteria": ["...", "..."],
      "validation": ["..."],
      "status": "pending"
    }
  ],
  "execution_order": ["TASK-001", "TASK-002", ...],
  "acceptance_criteria": ["...", "..."],
  "validation_steps": ["Lint and build verification", ...],
  "risks": [...],
  "estimated_complexity": {...}
}
```

---

## Duplicate Work Prevention

Before generating a plan, the Planner MUST check:

- ✅ Has this milestone already been implemented? (Check `docs/09_COMPLETED_TASKS.md`)
- ✅ Has part of the requested feature already been implemented?
- ✅ Are the required APIs already available?
- ✅ Does the requested frontend route already exist?
- ✅ Does the requested component already exist?
- ✅ Are there existing tests?
- ✅ Are there existing documentation entries?

If work already exists, the Planner marks tasks as:
- `completed` - Work already done
- `pending` - Work still needed
- `requires_review` - Needs human verification

---

## Error Handling

The Planner handles these error cases:

| Error Condition | Response |
|----------------|----------|
| Empty user request | Return error plan with "Empty request" message |
| Invalid request | Request clarification via Orchestrator |
| Missing documentation | Log warning, continue with available docs |
| Unknown agent role | Warn and assign to fallback agent |
| Plan validation fails | Return INVALID status with issues list |

---

## Logging

The Planner logs to `ai_agents/logs/planner/`:

```
[PLANNER] Reading project documentation
[PLANNER] Inspecting current project state
[PLANNER] Creating execution plan
[PLANNER] Plan saved to state
[PLANNER] Plan validation completed
```

Actions are recorded in `ai_agents/state/actions.jsonl` with agent type `"planner"`.

---

## Usage

```bash
# Run planner directly with a request
python ai_agents/scripts/planner_agent.py --request "Implement Milestone 6.6 — Project Workspace Dashboard"

# Or run via Orchestrator (which invokes planner internally)
python ai_agents/scripts/orchestrator.py --task "..."
```

---

## State Files

### `ai_agents/state/planner/current_plan.json`

The current plan being worked on:

```json
{
  "plan_id": "...",
  "request": "...",
  "status": "PENDING|COMPLETE|INVALID",
  "tasks": [...],
  "milestone": "..."
}
```

---

## Text-Only LLM Check

The Planner sends only text, JSON, Markdown, code, and logs to Qwen 3.5:

- Images sent: NO
- Image input added: NO  
- Visual analysis attempted: NO

---

## Next Steps After This Task

After successful implementation:
1. Update project documentation
2. Document in `docs/09_COMPLETED_TASKS.md`
3. Add entry to `docs/11_CHANGELOG.md`
4. Begin STEP 18 — Debugging Agent Runtime
