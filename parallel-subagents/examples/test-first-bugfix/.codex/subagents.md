---
# Service with a mandatory "red test before fix" bug workflow and parallel hands.
language: Vietnamese
instruction_files: AGENTS.md, docs/CONTRIBUTING.md
parallelism: parallel
bug_workflow: red-test-first
verify: make -C backend test-fast
verify: make -C backend typecheck
---
- Every bug fix lands together with the regression test that was red before the fix.
- Run pytest with `backend/` as the working directory (`env -C backend .venv/bin/pytest -q <node>`).
- Never edit an applied database migration; add a new one instead.
- Never put `cd` inside a compound shell command; use absolute paths.
