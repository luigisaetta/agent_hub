---
Author: L. Saetta
Last modified: 2026-03-25
License: MIT
Description: Operational rules and quality standards for AI agents contributing to agent_hub.
---

# Agents.md

## Purpose
This file defines the roles of AI agents in the `agent_hub` project, their operational responsibilities, and the minimum quality rules for contributing consistently.

## Project Context
`agent_hub` is a collection of Python examples for OCI Generative AI using OpenAI-compatible APIs.

Main areas:
- `common/`: shared logic (clients, output, retrieval, model helpers)
- `examples/`: demo scripts and utilities
- `connectors/`: connector lifecycle management
- `tests/`: pytest suite with fixtures/fakes
- `docs/`: technical documentation

## Agent Roles

### 1) Maintainer Agent
Responsible for:
- proposing and applying code changes
- keeping consistency with repository structure and conventions
- updating documentation when behavior changes

### 2) Review Agent
Responsible for:
- identifying bugs, regressions, risks, and edge cases
- checking minimum test coverage for changes
- reviewing impacts on configuration and compatibility

### 3) Docs Agent
Responsible for:
- updating `README.md` and files in `docs/`
- adding reproducible usage examples
- keeping prerequisites, environment variables, and commands aligned

## Operating Rules
- Prefer small, focused changes.
- Do not introduce dependencies without a clear reason.
- Avoid hardcoding secrets, OCIDs, or keys.
- Keep scripts runnable from repository root (`python -m ...`).
- Every new Python file must include the standard project header at the top, conforming to the agreed template.
- Run `pylint` on changed Python files and resolve all warnings before considering a change ready.
- Run `pytest` and `pylint` using Conda environment `agent_hub` (for example: `conda run -n agent_hub python -m pytest` and `conda run -n agent_hub pylint ...`).
- Preserve backward compatibility of existing examples unless explicitly requested otherwise.

## Standard Workflow
1. Understand the task and identify impacted files.
2. Implement the minimum required change.
3. Update or add tests in `tests/` when behavior changes.
4. Run essential local checks (at minimum: `conda run -n agent_hub python -m pytest` on impacted tests, `conda run -n agent_hub python -m pylint` on changed Python files, and `conda run -n agent_hub python -m black` when code was edited).
5. Update documentation when needed.

## Quality Checklist (Definition of Done)
A change is considered ready when:
- relevant tests pass (`pytest` or targeted subset)
- `pylint` reports zero warnings on changed Python files
- code remains readable and consistent
- no obvious functional regressions are introduced
- documentation is updated if UX/config/commands changed

## Repository-Specific Conventions
- Python 3.11+
- testing with `pytest`
- runtime dependencies in `requirements.txt`
- test/dev dependencies in `requirements-dev.txt`
- use `set_env.sh` to select the active environment profile

## Useful Commands
```bash
# Basic setup
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Example run
python -m examples.example01

# Tests
conda run -n agent_hub python -m pytest -q

# Lint (changed files)
conda run -n agent_hub pylint path/to/changed_file.py
```

## Security and Configuration
- Credentials must remain outside the repository (local `.env.*` files).
- Environment variables override defaults in `config.py`.
- Before operations on shared resources (vector stores/connectors), verify the active environment with `./show_current_env.sh`.

## Escalation
Require human review when:
- a change impacts OCI authentication/authorization
- endpoints or behavior across preprod/prod are changed
- new scripts are introduced for bulk delete/update operations on resources

## Template for New Tasks
Use this format in tickets/prompts:
- Goal:
- Files involved:
- Constraints:
- Acceptance criteria:
- Required tests:
- Rollout notes:
