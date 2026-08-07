# Sanskriti AI Studio — Development Guidelines

**Version:** 1.0  
**Status:** Active  
**Last Updated:** 2026-07-30

## 1. Mandatory Development Workflow

Every development task follows:

```text
Read Documentation
 ↓
Understand Architecture
 ↓
Read Current Task
 ↓
Inspect Existing Code
 ↓
Plan
 ↓
Implement
 ↓
Test
 ↓
Fix Root Causes
 ↓
Validate
 ↓
Update Documentation
 ↓
Report
 ↓
Suggest Next Task
```

## 2. Documentation Reading Order

AI assistants must read:

1. `00_PROJECT_STORY.md`
2. `01_CODING_RULES.md`
3. `02_SYSTEM_ARCHITECTURE.md`
4. `03_DATABASE_DESIGN.md`
5. `04_API_SPECIFICATION.md`
6. `05_ROADMAP.md`
7. `06_CURRENT_TASK.md`
8. `07_DEVELOPMENT_GUIDELINES.md`
9. `08_AI_CONTEXT.md`
10. `09_COMPLETED_TASKS.md`
11. `10_NEXT_TASK.md`
12. `11_CHANGELOG.md`
13. `12_PROMPT_LIBRARY.md`
14. `13_DECISIONS.md`
15. `99_AI_INSTRUCTIONS.md`

## 3. Inspect Before Modify

Before coding:

- Inspect relevant files.
- Search for existing implementations.
- Check API routes.
- Check database models.
- Check frontend routes/components.
- Check tests.

Never assume a feature is missing.

## 4. Testing

Run relevant tests after changes.

Frontend:

```bash
npm run lint
npm run build
```

Backend commands must follow the project's configured tooling.

If a test fails:

1. Read the complete error.
2. Identify root cause.
3. Fix.
4. Re-run.
5. Repeat until successful or genuinely blocked.

## 5. Browser Verification

For UI work:

- Start backend.
- Start frontend.
- Open relevant route.
- Test real interactions.
- Check browser console.
- Check network/API calls.
- Verify refresh behavior.

If screenshots are required for visual analysis, use a vision-capable model.

Do not send screenshots to Qwen 3.5.

## 6. API Verification

Use Swagger for backend API verification where applicable.

Verify:

- Status codes.
- Response payload.
- Validation.
- Error handling.
- Persistence.

## 7. Git Workflow

The project uses Git.

The user's preferred shell is Git Bash.

Normal workflow:

```bash
git status
git add .
git commit -m "Describe change"
git push origin master
```

Always inspect status before committing.

Do not use force push unless explicitly requested.

## 8. Documentation

After implementation:

- Update current task.
- Append AI context.
- Append completed task.
- Update next task.
- Append changelog.

Preserve history.

## 9. AI Agent Workflow

Agents must:

- Have one clear responsibility.
- Produce structured results.
- Report failures honestly.
- Never claim unverified success.
- Avoid destructive operations without approval.

## 10. Development Environment

Prefer local services:

- LM Studio
- ComfyUI
- PostgreSQL
- FFmpeg

Do not hardcode local machine paths.

## 11. Performance

The current development PC has approximately:

- RTX 3060 12GB
- i7-14700F
- 32GB RAM

Be mindful of RAM and VRAM usage.

Avoid running multiple unnecessarily large local models simultaneously.

## 12. Final Report

Every completed task should report:

- Status
- Files created
- Files modified
- Tests
- Build
- API verification
- Remaining issues
- Documentation updates
- Recommended next task
