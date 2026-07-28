
==================================================
GLOBAL PROJECT RULES — MUST FOLLOW
==================================================

PROJECT:
Sanskriti AI Studio

CURRENT AI MODEL:
Qwen 3.5

IMPORTANT — TEXT-ONLY LLM:
Qwen 3.5 must ALWAYS be treated as a TEXT-ONLY LLM in this project.

NEVER:
- Send images to Qwen 3.5.
- Attach images to LLM requests.
- Use image input during architecture analysis.
- Add image input to prompts sent to Qwen 3.5.
- Add multimodal/image-processing functionality to the LLM integration.
- Convert images to base64 and send them to Qwen 3.5.
- Use image URLs as LLM input.

The LLM may process:
- Text
- Markdown
- JSON
- Code
- Project documentation
- Logs
- Error messages
- Terminal output

If visual/image analysis is required in a future milestone, STOP and report that Qwen 3.5 is TEXT-ONLY. Do not automatically implement image input.

==================================================
ARCHITECTURE SAFETY
==================================================

Before modifying code:

1. Read the existing project documentation.
2. Inspect the existing repository structure.
3. Inspect existing implementations.
4. Follow the current architecture.
5. Reuse existing services, utilities, API clients, database sessions, and configurations.
6. Do not create duplicate implementations.
7. Do not redesign the architecture.
8. Do not modify unrelated modules.
9. Do not invent files, APIs, tables, models, or relationships that do not exist.
10. Do not assume functionality exists without verifying it.

==================================================
GIT SAFETY
==================================================

Work ONLY on the current branch.

DO NOT:
- Switch branches.
- Merge master/main.
- Reset the repository.
- Revert commits.
- Force push.
- Delete branches.
- Modify Git configuration.

Do not perform Git operations unless explicitly instructed.

==================================================
DATABASE SAFETY
==================================================

Do not modify the database schema unless the milestone explicitly requires it.

Do not:
- Create unnecessary tables.
- Modify existing relationships.
- Change primary keys.
- Change foreign keys.
- Create unnecessary Alembic migrations.
- Hardcode database credentials.

Reuse the existing SQLAlchemy models and database configuration.

==================================================
VALIDATION
==================================================

After implementation:

1. Run the appropriate backend tests.
2. Run the appropriate frontend tests.
3. Run npm run lint.
4. Run npm run build.
5. Verify API endpoints through Swagger where applicable.
6. Verify database persistence where applicable.
7. Verify frontend functionality in the browser.

Do not report PASS unless the functionality was actually verified.

==================================================
FINAL REPORT
==================================================

Always report:

Status: PASS / FAIL / BLOCKED

What was implemented.

Files created.

Files modified.

Files deleted.

Tests executed.

Lint result.

Build result.

API verification result.

Database verification result.

Frontend verification result.

Known issues.

Remaining work.

TEXT-ONLY LLM CHECK:
- Images sent to Qwen 3.5: NO
- Image input added: NO