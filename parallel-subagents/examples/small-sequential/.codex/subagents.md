---
# Small project, one maintainer: hands run one at a time, no mandatory test-first rule.
language: Vietnamese
instruction_files: AGENTS.md, README.md
parallelism: sequential
bug_workflow: standard
verify: npm run lint
verify: npm test
---
- Keep changes minimal; this is a small CLI with no public API stability promise.
- Do not add dependencies without asking the brain.
- Format with `npm run format` before reporting.
