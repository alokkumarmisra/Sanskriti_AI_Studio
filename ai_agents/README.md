# AI Agent Development Workspace

## Purpose of ai_agents

This workspace provides an isolated environment for developing and managing AI agents within Sanskriti AI Studio. It is designed to enable autonomous agent capabilities while maintaining strict separation from the core frontend and backend application logic.

The `ai_agents/` directory serves as a dedicated sandbox where AI-powered automation can be developed, tested, and deployed without affecting existing project management features.

---

## Multi-Agent System Architecture

### How the Multi-Agent System Will Work

The multi-agent system will operate as follows:

```
┌─────────────────────────────────────────────────────────────┐
│                    AI AGENT SYSTEM                           │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Orchestrator│──→│   Planner    │──→│   Executor    │  │
│  │              │    │              │    │              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│          ▲              ▲               ▲                    │
│          │              │               │                    │
│       State Manager   Agent Registry   Task Queue            │
└─────────────────────────────────────────────────────────────┘
```

1. **Orchestrator**: Coordinates agent activities and manages overall workflow
2. **Planner**: Breaks down tasks into actionable steps for individual agents
3. **Executor**: Performs specific tasks assigned to each agent type
4. **State Manager**: Maintains persistent state across agent interactions
5. **Agent Registry**: Tracks available agents and their capabilities
6. **Task Queue**: Manages incoming requests and distributes work

---

## Planned Agents

### Phase 1 - Foundation Agents

1. **Project Manager Agent**
   - Creates new projects with proper structure
   - Initializes project configuration
   - Validates project requirements

2. **Content Researcher Agent**
   - Researches topic information
   - Gathers context for content generation
   - Sources reference materials

3. **Script Writer Agent**
   - Drafts initial scripts based on research
   - Refines content with user feedback
   - Optimizes for target audience

4. **Video Planner Agent**
   - Creates shot lists
   - Plans visual sequences
   - Estimates production timeline

5. **Quality Review Agent**
   - Validates all generated content
   - Ensures quality standards
   - Suggests improvements

6. **Review / Code Quality Agent**
   - Reviews code changes after Coding Agent implementation and Testing Agent validation
   - Checks correctness, architecture, backend, frontend, database, API, security, testing, and documentation requirements
   - Produces `PASS`, `NEEDS_CHANGES`, or `FAIL` in `ai_agents/state/review_report.json`
   - Never modifies source code and never performs browser screenshot or image analysis

### Phase 2 - Advanced Agents

6. **Style Transfer Agent**
   - Applies artistic styles to visuals
   - Consistent style across projects

7. **Localization Agent**
   - Handles multi-language support
   - Cultural adaptation of content

8. **Analytics Agent**
   - Monitors project performance
   - Generates insights and reports

---

## Agent Communication Protocols

### Inter-Agent Communication

Agents communicate through:

1. **Shared State Store**
   - JSON-based state files in `ai_agents/state/`
   - Each agent maintains its own state namespace
   - Shared read-write memory for collaboration

2. **Event Bus Pattern**
   - Agents publish events to shared topics
   - Events are logged in `ai_agents/logs/`
   - Other agents subscribe to relevant events

3. **Message Queue**
   - Tasks flow through `ai_agents/scripts/` for processing
   - Script-based orchestration ensures reliability

### Communication Flow Example

```
User Request → Planner Agent → Task Breakdown → Coding Agent → Testing Agent → Review Agent → Final Output
```

Each agent reads/writes to the shared state, creating an audit trail of all operations.

---

## Relationship Between Components

### Cline (Development Environment)

- **Role**: Primary development assistant for initial AI agent implementation
- **Access**: Full access to `ai_agents/` directory
- **Responsibilities**: 
  - Creating agent code and logic
  - Writing prompts and configurations
  - Building state management systems
  - Implementing communication protocols

### LM Studio

- **Role**: Local LLM inference engine for agents
- **Access**: Connected via environment configuration
- **Usage**: 
  - Text generation for all agents
  - Prompt-based agent behavior
  - Reasoning and planning tasks

### Qwen 3.5 (Text-Only Model)

- **Role**: Primary reasoning model for agent intelligence
- **CRITICAL RULE**: Qwen 3.5 is TEXT-ONLY only
- **Access**: Via LM Studio interface
- **Capabilities**:
  - Text generation and understanding
  - Logic, planning, and reasoning
  - Code generation and review
  - Agent coordination tasks

### Vision Model (Future)

- **Status**: Not yet integrated
- **Planned Use**: Visual analysis, image/video processing agents
- **Implementation**: Will be added after text-only foundation is stable
- **Integration**: Will require new agent types with visual capabilities

---

## Directory Structure

```
ai_agents/
├── agents/          # Agent implementations and code
│   ├── __init__.py
│   ├── base.py      # Base agent classes
│   ├── orchestrator.py
│   ├── planner.py
│   ├── executor.py
│   └── [agent-specific files]
│
├── prompts/         # Agent prompts and instructions
│   ├── system_prompts/
│   ├── task_prompts/
│   └── [agent-specific prompts]
│
├── state/           # Persistent agent state
│   ├── projects/    # Project-related agent state
│   ├── tasks/       # Task execution state
│   └── [agent-specific state files]
│
├── logs/            # Agent operation logs
│   ├── events/      # Event logs
│   └── errors/      # Error logs
│
└── scripts/         # Orchestration and utility scripts
    ├── orchestrate.py
    ├── monitor.py
    ├── coder_agent.py
    ├── tester_agent.py
    ├── reviewer_agent.py
    └── [utility scripts]
```

---

## Review / Code Quality Agent Runtime

The Review / Code Quality Agent runtime is implemented at:

```text
ai_agents/scripts/reviewer_agent.py
```

It reuses the existing LM Studio configuration and text-only client:

```text
ai_agents/scripts/config.py
ai_agents/scripts/lmstudio_client.py
```

### Inputs

The runtime reads available shared state:

- `ai_agents/state/task_plan.json` or `ai_agents/state/current_task.json`
- `ai_agents/state/coding_result.json`, `coder_result.json`, or `code_report.json`
- `ai_agents/state/test_report.json`
- Optional structured input passed with `--input`

Review input may include task description, milestone, acceptance criteria, changed files, git diff, relevant source code, test results, build results, lint results, backend validation, database migration status, API verification, and documentation changes.

### Outputs

The runtime writes:

```text
ai_agents/state/review_report.json
ai_agents/state/actions.jsonl
```

The review report uses:

```json
{
  "status": "PASS | NEEDS_CHANGES | FAIL",
  "summary": "Review summary.",
  "findings": [],
  "warnings": [],
  "recommendations": [],
  "files_reviewed": [],
  "acceptance_criteria": {
    "passed": [],
    "failed": []
  }
}
```

### Runtime Commands

```bash
python ai_agents/scripts/reviewer_agent.py
python ai_agents/scripts/reviewer_agent.py --input ai_agents/state/review_input.json
python ai_agents/scripts/reviewer_agent.py --include-git-diff
```

`--include-git-diff` performs a non-destructive diff limited to `ai_agents/` changes. The default runtime does not require Git diff and can consume a supplied diff from structured input instead.

### Qwen 3.5 Text-Only Boundary

The Review Agent sends only text, Markdown, JSON, code snippets, diffs, logs, and terminal output to Qwen 3.5. It never sends images, screenshots, image files, image URLs, browser screenshots, or base64 image data. Visual/browser analysis belongs to a separate Vision Agent.

---

## Critical Development Rules

### Qwen 3.5 Text-Only Rule

**Qwen 3.5 is TEXT-ONLY in this project.**

- Never send images, screenshots, or image files to Qwen 3.5
- Do not implement image input functionality for Qwen 3.5
- All visual analysis must use alternative methods (image descriptions, metadata)
- This rule applies across all agents and system components

### Isolation Rule

**This workspace must not interfere with frontend/backend application code.**

- Do NOT modify `frontend/` directory
- Do NOT modify `backend/` directory
- Do NOT change existing APIs or schemas
- Do NOT alter database schema
- All agent operations use separate state stores in `ai_agents/state/`
- Agents communicate through defined interfaces, not direct file access

### Git Safety Rule

- Never commit changes to unrelated files
- Never reset, delete, or modify Git history
- Create new files only within `ai_agents/`
- Existing project files remain unchanged

---

## Getting Started

### 1. Configure Agent Connections

Edit `backend/.env` (if needed) to set:

```
# AI Model Configuration
LM_STUDIO_URL=http://localhost:1234
QWEN_3_5_MODEL=qwen/qwen2.5-coder-7b-instruct

# Agent State Directory
AGENT_STATE_DIR=ai_agents/state
AGENT_LOGS_DIR=ai_agents/logs
```

### 2. Create First Agent

Place agent code in `ai_agents/agents/` following the base class pattern:

```python
from agents.base import BaseAgent

class ProjectManagerAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__(config)
    
    async def create_project(self, project_data: dict) -> dict:
        # Agent implementation
        pass
```

### 3. Define Prompts

Add system prompts in `ai_agents/prompts/system_prompts/`:

```yaml
# prompts/system_prompts/project_manager.yaml
name: Project Manager Agent
system_prompt: |
  You are the Project Manager Agent responsible for...
role: orchestrator
```

### 4. Initialize State

Run initialization script:

```bash
python ai_agents/scripts/orchestrate.py --init
```

---

## Future Roadmap

- [ ] Implement Base Agent framework
- [ ] Create Orchestrator agent
- [ ] Build Planner agent with task decomposition
- [ ] Develop Executor agents for specific tasks
- [ ] Implement state persistence layer
- [ ] Add event logging and monitoring
- [ ] Create API endpoints for agent control
- [ ] Integrate Vision Model capabilities (Phase 2)

---

## Maintenance

### Log Rotation

Logs in `ai_agents/logs/` should be rotated:

```bash
# Rotate logs older than 30 days
find ai_agents/logs -type f -mtime +30 -delete
```

### State Cleanup

Periodic cleanup of old state files:

```bash
# Keep last 10 state snapshots per agent
find ai_agents/state -name "*snapshot*" | sort | tail -n +11 | xargs rm
```

---

## Support

For questions about the AI agent system, refer to:
- `docs/01_AGENTS.md` for development rules
- `docs/02_ARCHITECTURE.md.md` for system architecture
- `ai_agents/README.md` (this file) for workspace-specific information

---

*This workspace is dedicated to developing intelligent automation without affecting core application functionality.*
