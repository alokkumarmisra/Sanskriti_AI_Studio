# Sanskriti AI Studio — AI Operating Instructions

**Version:** 1.0  
**Status:** MANDATORY  
**Last Updated:** 2026-07-30

# IMPORTANT

These instructions apply to every AI coding assistant and development agent working on Sanskriti AI Studio.

The AI must treat the project documentation as the source of truth.

## 1. Documentation Must Be Read First

Before modifying code, read:

```text
docs/00_PROJECT_STORY.md
docs/01_CODING_RULES.md
docs/02_SYSTEM_ARCHITECTURE.md
docs/03_DATABASE_DESIGN.md
docs/04_API_SPECIFICATION.md
docs/05_ROADMAP.md
docs/06_CURRENT_TASK.md
docs/07_DEVELOPMENT_GUIDELINES.md
docs/08_AI_CONTEXT.md
docs/09_COMPLETED_TASKS.md
docs/10_NEXT_TASK.md
docs/11_CHANGELOG.md
docs/12_PROMPT_LIBRARY.md
docs/13_DECISIONS.md
docs/99_AI_INSTRUCTIONS.md
```

Read them in this order.

## 2. Current Task Has Priority

After reading documentation:

1. Read `06_CURRENT_TASK.md`.
2. Read `10_NEXT_TASK.md`.
3. Inspect the actual repository.
4. Implement only the active task.

Never implement future milestones automatically.

## 3. Existing Code

Always inspect existing code before creating new code.

Do not:

- Duplicate functionality.
- Duplicate API clients.
- Duplicate database connections.
- Recreate existing components.
- Replace working functionality unnecessarily.

## 4. Preserve Completed Work

Do not break:

- Milestone 6.1.
- Milestone 6.2.
- Milestone 6.3.
- Milestone 6.4.
- Milestone 6.5.

Regression testing is mandatory for affected functionality.

## 5. Qwen 3.5 — MANDATORY TEXT-ONLY RULE

Qwen 3.5 is TEXT-ONLY.

NEVER send Qwen 3.5:

- Images.
- Screenshots.
- Browser screenshots.
- Image URLs.
- Image files.
- Base64 encoded images.

This rule applies to:

- Analysis.
- Reasoning.
- Text generation.
- Coding tasks.
- Browser analysis.

If visual analysis is needed, use a separate vision-capable model.

## 6. Development Workflow

Follow:

```text
Read Docs
 ↓
Read Current Task
 ↓
Inspect Code
 ↓
Plan
 ↓
Implement
 ↓
Run Tests
 ↓
Fix Root Cause
 ↓
Re-run
 ↓
Update Docs
 ↓
Final Report
```

## 7. Testing

Never claim PASS without actually verifying.

Frontend:

```bash
npm run lint
npm run build
```

Backend:

Use the project's existing backend validation commands.

API:

Use Swagger where applicable.

Browser:

Verify real user workflows where applicable.

## 8. Error Handling

Never hide or suppress errors.

If an error occurs:

1. Capture the complete error.
2. Diagnose root cause.
3. Fix root cause.
4. Re-run.
5. Verify.

## 9. Git Safety

The repository has been freshly initialized.

Primary branch:

```text
master
```

Never automatically:

- Delete `.git`.
- Reset Git history.
- Force push.
- Delete branches.
- Delete repository.
- Recreate repository.

The user prefers Git Bash commands.

## 10. Database Safety

Never:

- Delete database data automatically.
- Drop tables automatically.
- Modify schema without migrations.
- Hardcode credentials.

Seed data must be idempotent.

## 11. Documentation Policy

After code changes, update relevant documentation.

Append to:

- `08_AI_CONTEXT.md`
- `09_COMPLETED_TASKS.md`
- `11_CHANGELOG.md`

Update:

- `06_CURRENT_TASK.md`
- `10_NEXT_TASK.md`

Preserve historical information.

## 12. Agent Behavior

Agents must:

- Stay within assigned scope.
- Work from documentation.
- Report actual status.
- Report failures honestly.
- Never fabricate test results.
- Never claim a file was modified unless it was actually modified.
- Never claim an API passed unless verified.

## 13. Destructive Operations

Require explicit user approval before:

- Deleting repositories.
- Deleting branches.
- Resetting history.
- Force pushing.
- Dropping databases.
- Deleting production data.
- Removing large portions of the codebase.

## 14. Final Report

Every task must report:

```text
Status
Implementation Summary
Files Created
Files Modified
Tests
Lint
Build
API Verification
Backend Validation
Documentation Updated
Remaining Issues
Recommended Next Task
```

## 15. Milestone Completion Rule

A milestone can be marked COMPLETE only when:

- Required implementation exists.
- Acceptance criteria are verified.
- Relevant tests pass.
- Lint/build pass where applicable.
- Documentation is updated.
- No known blocking issue remains.

## 16. Ultimate Rule

Do not restart the project.

Do not rewrite working architecture without justification.

Do not implement future milestones without instruction.

Do not send images to Qwen 3.5.

Read the documentation.

Understand the code.

Make the smallest correct change.

Test it.

Document it.

Report the truth.
