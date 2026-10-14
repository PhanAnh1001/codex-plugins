---
name: parallel-subagents
description: Parallel subagent orchestration - the root session (brain) splits a task into bounded briefs, runs several `hand` worker subagents in parallel, then reviews and synthesizes their results. Use for any multi-step coding task that can be split across subagents in a repo that enables parallel-subagents.
---

# Parallel subagents: orchestration

The hooks inject a short version of this policy. This skill is the full reference and also the fallback
when hooks are disabled or untrusted (Codex asks you to trust non-managed hooks via `/hooks`).

## Roles

- **Brain (root session, orchestrator):** runs independent hands in parallel, clarifies the request, splits it, decides scope/design, reviews every hand's
  output, and writes the final answer. It does not grep/read/edit source itself, except plan/spec documents
  the project reserves for the brain, and reading diffs for review.
- **Hand (`hand` worker subagent):** executes exactly one self-contained brief and returns an evidence report.
  It never spawns agents, reviews, commits or pushes.

## Brief template

Every hand spawn uses this template (`templates/hand-brief.md`):

```
GOAL: <one sentence: the outcome to reach>
CONTEXT: <what the brain already knows, with file:line; assumptions already settled>
WRITE SCOPE: <files/directories the hand may create or modify> | READ-ONLY
DO NOT TOUCH: <forbidden files/directories/commands>
MANDATORY RULES: <repo rules copied VERBATIM>
VERIFY: <commands to run / criteria for done>
RETURN: <report format>
```

- **Fail-closed:** no WRITE SCOPE means READ-ONLY.
- **Copy rules verbatim.** The SubagentStart hook injects `.codex/subagents.md` into each hand, but any other repo
  rule the task depends on must be pasted into MANDATORY RULES.

## Follow-up rule

When the next task touches the files/module a finished hand just worked on, send it a delta brief instead of
spawning a new hand (its context and prompt cache are still warm). Spawn a new hand for independent work,
another area, a hand whose context has grown large, or while the old hand is still running. If the Codex
build cannot message a finished agent, spawn a new hand and paste the relevant findings into CONTEXT.

## Review rule

Review belongs to the brain: after a hand reports a write, read the diff (`git diff`) or changed files before
reporting to the user. Never delegate review. On a finding, send the fix back (preferably to the same hand)
and review again. Re-check every claim a hand makes against files or command output before accepting it.

## Parallelism and the project's bug workflow

Configured per project in `.codex/subagents.md` (`parallelism`, `bug_workflow`); see the plugin README.
