# Repository Guidelines

## Project Structure and Module Organization
- Core app code lives at the repo root (e.g., `main.py`, `crawler.py`, `tester.py`, `report_generator.py`, `models.py`).
- Configuration is in `config.py`.
- Reports and artifacts are written to `test_results/` (HTML report, JSON, screenshots).
- Tests live under `tests/` and follow pytest conventions (see below).

## Build, Test, and Development Commands
- `python main.py`: run the full Playwright-driven test flow and generate the HTML report.
- `python smoke_test.py`: quick smoke test to load the homepage and check for console errors.
- `python -m pytest -q`: run automated tests from the `tests/` folder.

## Coding Style and Naming Conventions
- Python with 4-space indentation.
- Use `snake_case` for variables/functions and `CamelCase` for classes.
- Keep functions focused and avoid long, nested logic where possible.
- Prefer small, descriptive helper functions for readability.

## Testing Guidelines
- Testing framework: pytest.
- Test files should be named `test_*.py` and live in `tests/`.
- Keep tests fast and deterministic (no network unless explicitly required).
- Run `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q` before submitting changes to avoid global plugin conflicts.

## Commit and Pull Request Guidelines
- Use Conventional Commits (e.g., `feat: ...`, `fix: ...`, `docs: ...`).
- PRs should include a short summary, how to test, and relevant screenshots or logs if reporting changes affect output.
- If you change configuration or reporting, note the expected behavior in the PR description.

## Security and Configuration Notes
- Do not edit `.env*` files inside the repo.
- Treat URLs and credentials as sensitive; keep secrets out of source control.

## Standard Workflow (SOP)
Use this workflow for all non-trivial tasks. Keep each step short and explicit.

### Step 1: Task Definition (Human)
- Goal: what success looks like.
- Scope: what is included/excluded.
- Risk areas: auth, tenancy, payments, data loss, migrations, performance.
- Acceptance criteria: tests to pass or behaviors to verify.

### Step 2: Plan First (Agent -> Human)
- List files/modules to touch.
- List commands intended to run.
- List tests intended to run.
- Note expected side effects.
- Human approves the plan before changes.

### Step 3: Execute With Evidence (Agent)
- Provide a diff summary.
- List commands run and outputs.
- List tests run and results.
- Note any errors and fixes applied.

### Step 4: Audit Loop (Required)
- Security/RBAC implications.
- Data integrity and migrations.
- Regression risks.
- Missing tests.
- Rollback plan.

### Step 5: Human Understanding (Mandatory in PR)
- What changed and why (human words).
- One real risk in this change.
- One thing personally verified.
- One thing still uncertain or to watch.

### Step 6: PR Submission Requirements
- Link to ticket/task.
- Summary of changes.
- Audit output attached or summarized.
- Proof artifacts (tests/logs/screenshots).
- Human Understanding section.
- Rollback note.
