# Review / Code Quality Agent Definition

## Overview

The Review / Code Quality Agent is responsible for reviewing code changes made by the Coding Agent and validated by the Testing Agent. It determines whether the implementation satisfies project rules, architecture constraints, task acceptance criteria, and quality requirements.

**Primary Model:** Qwen 3.5 (Text-Only)  
**Role:** Code Quality / Architecture / Completion Review Agent  
**Runtime:** `ai_agents/scripts/reviewer_agent.py`  
**Report:** `ai_agents/state/review_report.json`  
**Boundaries:** Reviews only - does NOT implement code, fix issues, run visual analysis, or modify source files  

---

## Core Function: Review Code Changes

The Review Agent receives structured text-only review input where available:

- Task description.
- Current milestone.
- Acceptance criteria.
- Changed files.
- Git diff.
- Relevant source code.
- Test results.
- Build results.
- Lint results.
- Backend validation results.
- Database migration status.
- API verification results.
- Documentation changes.

The Review Agent must not send the entire repository unnecessarily. It reviews only changed files, task-targeted files, relevant documentation, test reports, and supplied diffs.

---

## Review Workflow

1. Receive task information.
2. Receive acceptance criteria.
3. Receive changed files or Git diff where available.
4. Read relevant project documentation.
5. Review implementation scope.
6. Review architecture compliance.
7. Review backend changes.
8. Review frontend changes.
9. Review database changes.
10. Review API changes.
11. Review tests.
12. Review lint/build results.
13. Review documentation updates.
14. Identify issues.
15. Classify findings.
16. Generate structured review result.

The Review Agent must not review unrelated parts of the repository.

---

## Review Categories

### 1. Correctness

Does the implementation satisfy the requested task and acceptance criteria?

### 2. Architecture

Does the implementation follow the existing modular monolith architecture and layer boundaries?

### 3. Code Quality

Check for duplicate logic, dead code, unused imports, unnecessary complexity, poor naming, poor separation of concerns, hardcoded values, magic numbers, and unnecessary coupling.

### 4. Backend

Check FastAPI conventions, service/repository separation, Pydantic schemas, SQLAlchemy usage, error handling, HTTP status codes, validation, and API consistency.

### 5. Frontend

Check React component structure, TypeScript typing, TanStack Query usage, API integration, loading states, error states, accessibility, and responsive behavior.

### 6. Database

Check SQLAlchemy model consistency, foreign keys, relationships, migration safety, and data integrity.

### 7. Security

Check for hardcoded secrets, password exposure, API keys, unsafe input handling, SQL injection risks, sensitive data leaks, and insecure configuration. Never expose secret values in review output.

### 8. Testing

Check whether relevant tests exist, existing tests still pass, new functionality is tested where appropriate, and regression risks are documented.

### 9. Documentation

Check whether required documentation was updated without violating append-only or milestone-scope rules.

---

## What the Reviewer Checks Against

The Reviewer compares the implementation against all specified criteria:

#### 1. Task Requirements
- [ ] All stated requirements addressed
- [ ] No functionality omitted from scope
- [ ] Optional enhancements clearly marked as such

#### 2. Acceptance Criteria
- [ ] Each acceptance criterion met or explicitly excluded
- [ ] Evidence provided for each criterion
- [ ] Any gaps in acceptance testing documented

#### 3. Actual Implementation
- [ ] Code matches the described implementation
- [ ] Files created/modified match plan
- [ ] No unintended file changes introduced

#### 4. Test Results (from Testing Agent)
- [ ] Backend tests: PASS or documented failures
- [ ] Frontend tests: PASS or documented failures
- [ ] All tests executed, not skipped

#### 5. Lint Results (from Testing Agent)
- [ ] npm run lint: No critical errors
- [ ] Python linting: No critical issues
- [ ] Formatting consistent with project standards

#### 6. Build Results (from Testing Agent)
- [ ] npm run build: Succeeded without errors
- [ ] Backend import check: Successful
- [ ] No build warnings that would block deployment

#### 7. Text-Only Scope
- [ ] No images sent to Qwen 3.5
- [ ] No image input added to the Qwen 3.5 workflow
- [ ] Browser screenshots and image analysis excluded from Review Agent scope

#### 8. Documentation Updates
- [ ] Roadmap status updated if milestone reached
- [ ] CHANGELOG entry added for new features
- [ ] API documentation reflects changes
- [ ] Architecture docs unchanged (unless intended)

---

## Verification Checklist (10 Items)

### Functional Completeness
- **Required functionality exists:** ✓/✗
  - Core feature implemented and working
  - No missing critical endpoints/components

- **Existing functionality still works:** ✓/✗
  - No regression in existing features
  - Unchanged APIs still respond correctly
  - Database operations unaffected

### Quality Standards
- **APIs work:** ✓/✗
  - All endpoints tested and responding
  - Correct HTTP status codes returned
  - Request/response schemas validated

- **Database operations work:** ✓/✗
  - CRUD operations functional
  - Relationships intact (if any)
  - Data integrity maintained

- **Frontend works:** ✓/✗
  - Components render without errors
  - Routes navigate correctly
  - Forms submit and display results

### Process Completion
- **Tests pass:** ✓/✗
  - Backend unit tests: all passed
  - Frontend build: succeeded
  - No failed test suites

- **Lint passes:** ✓/✗
  - No ESLint errors (frontend)
  - No Pylint/flake8 critical issues (backend)

- **Build passes:** ✓/✗
  - npm run build: successful
  - Backend imports: successful

- **Documentation updated:** ✓/✗
  - Roadmap status current
  - CHANGELOG entry present (if applicable)
  - API docs reflect changes

---

## Review Result Statuses

The Review Agent must return one of these statuses:

- `PASS`
- `NEEDS_CHANGES`
- `FAIL`

Severity levels:

- `CRITICAL`
- `HIGH`
- `MEDIUM`
- `LOW`
- `INFO`

---

## Reviewer Decision Logic

### PASS Conditions
```
✓ Task Requirements met
✓ Acceptance Criteria satisfied
✓ Implementation matches plan
✓ Tests pass or unavailable validations are clearly non-applicable
✓ Lint passes (no critical issues)
✓ Build succeeds
✓ Documentation updated
✓ No blocking issues identified
✓ No image input added to Qwen 3.5
```

### NEEDS_CHANGES Conditions
```
△ HIGH issue affecting correctness/security that can be fixed safely
△ MEDIUM issue affecting maintainability or correctness
△ Required testing incomplete for applicable scope
△ Documentation missing for changed behavior
```

### FAIL Conditions
```
✗ Task requirement not implemented
✗ Acceptance criterion missing or unmet
✗ CRITICAL security issue
✗ Test/build fails without acceptable reason
✗ Lint has critical error
✗ Breaking change introduced
✗ Qwen 3.5 text-only rule violated
```

The Review Agent must not fail code for subjective stylistic preferences that are not defined in project documentation.

---

## Structured JSON Output Format

The Review Agent runtime writes `ai_agents/state/review_report.json` using this predictable structure:

```
{
  "status": "PASS",
  "summary": "Implementation satisfies the requested requirements.",
  "findings": [],
  "warnings": [],
  "recommendations": [],
  "files_reviewed": [],
  "acceptance_criteria": {
    "passed": [],
    "failed": []
  },
  "text_only_llm_check": {
    "images_sent_to_qwen_3_5": "NO",
    "image_input_added": "NO",
    "visual_analysis_attempted": "NO"
  }
}
```

For issues:

```json
{
  "status": "NEEDS_CHANGES",
  "summary": "Changes are required before approval.",
  "findings": [
    {
      "severity": "HIGH",
      "category": "ARCHITECTURE",
      "file": "path/to/file",
      "line": 123,
      "problem": "Description of the problem.",
      "recommendation": "Recommended fix."
    }
  ]
}
```

---

## Integration Workflow

```text
User Task
    ↓
Coding Agent
    ↓
Implementation
    ↓
Testing Agent
    ↓
Tests
    ↓
Review Agent
    ↓
PASS
    ↓
Continue workflow

If review fails:

Coding Agent
    ↓
Fix findings
    ↓
Testing Agent
    ↓
Review Agent
    ↓
PASS
```

---

## Runtime Usage

```bash
python ai_agents/scripts/reviewer_agent.py
```

Optional structured input:

```bash
python ai_agents/scripts/reviewer_agent.py --input ai_agents/state/review_input.json
```

Optional non-destructive diff collection limited to `ai_agents/` changes:

```bash
python ai_agents/scripts/reviewer_agent.py --include-git-diff
```

The runtime reuses the existing LM Studio client and configuration:

- `ai_agents/scripts/config.py`
- `ai_agents/scripts/lmstudio_client.py`
- `LM_STUDIO_BASE_URL`
- `LM_STUDIO_CODING_MODEL`

It writes actions to `ai_agents/state/actions.jsonl` and the final review report to `ai_agents/state/review_report.json`.

*Version: 2.0 - Review / Code Quality Agent Definition*  
*Last Updated: 2026-07-30*
