#!/usr/bin/env python3
"""Emit parallel-subagents orchestration policy as Codex hook context.

Usage: subagents_policy.py {session-start|user-prompt|subagent-start}  (hook event JSON on stdin)

Generic policy lives here; project-specific settings come from `<cwd>/.codex/subagents.md`
(front matter `key: value` lines between `---` fences, then a free-form Markdown body of
project rules). Every setting has a default, so the plugin works with no project file.
Standard library only, compatible with the macOS system python3 (3.9).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_CONFIG_RELATIVE_PATH = Path(".codex") / "subagents.md"
FRONT_MATTER_FENCE = "---"
BRIEF_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "hand-brief.md"
# Agent role name that receives hand rules instead of brain routing policy.
HAND_AGENT_TYPE = "hand"
# Candidate stdin keys naming the agent role; the exact key Codex sends is not verified.
AGENT_TYPE_KEYS = ("agent_type", "agent_name", "subagent_type")
LIST_SEPARATOR = ","


class Event(str, Enum):
    SESSION_START = "session-start"
    USER_PROMPT = "user-prompt"
    SUBAGENT_START = "subagent-start"


# Must match "additionalContextLimit" per event in hooks/hooks.json. Codex counts that limit in
# tokens; we compare it against characters, which is conservative (a token is >= 1 char).
CONTEXT_LIMITS: Dict[Event, int] = {
    Event.SESSION_START: 2500,
    Event.USER_PROMPT: 1200,
    Event.SUBAGENT_START: 2500,
}

HOOK_EVENT_NAMES: Dict[Event, str] = {
    Event.SESSION_START: "SessionStart",
    Event.USER_PROMPT: "UserPromptSubmit",
    Event.SUBAGENT_START: "SubagentStart",
}


class BugWorkflow(str, Enum):
    STANDARD = "standard"
    RED_TEST_FIRST = "red-test-first"


class Parallelism(str, Enum):
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


@dataclass
class ProjectConfig:
    language: str = "Vietnamese"
    instruction_files: List[str] = field(default_factory=lambda: ["AGENTS.md"])
    parallelism: Parallelism = Parallelism.PARALLEL
    bug_workflow: BugWorkflow = BugWorkflow.STANDARD
    verify: List[str] = field(default_factory=list)
    rules: str = ""
    source: Optional[Path] = None
    warnings: List[str] = field(default_factory=list)


def _split_list(value: str) -> List[str]:
    return [item.strip() for item in value.split(LIST_SEPARATOR) if item.strip()]


def _apply_setting(config: ProjectConfig, key: str, value: str) -> None:
    if key == "language":
        config.language = value
    elif key == "instruction_files":
        config.instruction_files = _split_list(value)
    elif key == "parallelism":
        config.parallelism = Parallelism(value)
    elif key == "bug_workflow":
        config.bug_workflow = BugWorkflow(value)
    elif key == "verify":
        config.verify.append(value)
    else:
        config.warnings.append(f"unknown key '{key}' ignored")


def _parse_front_matter(config: ProjectConfig, lines: List[str]) -> None:
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, sep, value = stripped.partition(":")
        if not sep:
            config.warnings.append(f"line without ':' ignored: {stripped}")
            continue
        try:
            _apply_setting(config, key.strip(), value.strip())
        except ValueError:
            config.warnings.append(f"invalid value for '{key.strip()}': {value.strip()}")


def load_project_config(cwd: Path) -> ProjectConfig:
    config = ProjectConfig()
    path = cwd / PROJECT_CONFIG_RELATIVE_PATH
    if not path.is_file():
        return config
    config.source = path
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        config.warnings.append(
            f"cannot read {path} ({type(error).__name__}); using defaults"
        )
        return config
    if lines and lines[0].strip() == FRONT_MATTER_FENCE:
        try:
            end = lines.index(FRONT_MATTER_FENCE, 1)
        except ValueError:
            config.warnings.append("front matter not closed; whole file treated as rules")
            config.rules = "\n".join(lines).strip()
            return config
        _parse_front_matter(config, lines[1:end])
        lines = lines[end + 1 :]
    config.rules = "\n".join(lines).strip()
    return config


def _bug_rule(config: ProjectConfig) -> str:
    if config.bug_workflow is BugWorkflow.RED_TEST_FIRST:
        return (
            "Bug investigation: the brief MUST require (1) git history of the area "
            "(git log/blame) to find earlier fixes, reverts and regression tests, and (2) the "
            "smallest test reproducing the bug, failing for the right reason (an assertion on "
            "the wrong behavior; an import error does not count), BEFORE any fix."
        )
    return "Bug investigation: the brief asks the hand to reproduce before fixing."


def _parallel_rule(config: ProjectConfig) -> str:
    if config.parallelism is Parallelism.SEQUENTIAL:
        return "Run hands one at a time; start the next brief only after reviewing the last."
    return (
        "Run independent hands in parallel by layer/module/question; serialize only when "
        "two hands would touch the same file."
    )


def _rules_pointer(config: ProjectConfig) -> str:
    return (
        f"Project rules are too long to inline ({len(config.rules)} chars); "
        f"read {config.source} in full before starting."
    )


def _project_block(config: ProjectConfig, inline_rules: bool = True) -> str:
    parts = [f"Project instruction files: {', '.join(config.instruction_files)}."]
    parts.append(f"Reply language for reports: {config.language}.")
    if config.verify:
        parts.append("Verification commands: " + "; ".join(config.verify) + ".")
    if config.rules and inline_rules:
        parts.append("Project rules (from .codex/subagents.md):\n" + config.rules)
    elif config.rules:
        parts.append(_rules_pointer(config))
    for warning in config.warnings:
        parts.append(f"[parallel-subagents config warning] {warning}")
    return "\n".join(parts)


def session_start_text(config: ProjectConfig, inline_rules: bool = True) -> str:
    brief = BRIEF_TEMPLATE_PATH.read_text(encoding="utf-8").strip()
    return f"""PARALLEL-SUBAGENTS POLICY (parallel subagent orchestration) - BRIEF TEMPLATE (mandatory when spawning a `hand` agent; fill every field, briefly):
{brief}
A brief without WRITE SCOPE is READ-ONLY for the hand (fail-closed).

FOLLOW-UP RULE: when the next task touches the same files/module a finished hand just read or
edited, send the follow-up to that hand (a delta brief in the same template) instead of spawning a
new one, if this Codex build supports messaging an existing agent. Spawn a NEW hand when the work is
independent or in another area, when the old hand's context has grown large, or while the old hand
is still running.

REVIEW RULE: review is the brain's job. After a hand reports a write, the brain reads the diff /
changed files itself before reporting to the user. Never delegate review to a hand. If review finds
a problem, send the fix back (preferably to the same hand), then review again.

{_project_block(config, inline_rules)}"""


def user_prompt_text(config: ProjectConfig, inline_rules: bool = True) -> str:
    return (
        "PARALLEL-SUBAGENTS POLICY (parallel subagent orchestration): the root session is the brain/orchestrator - "
        "it splits work, decides, reviews and synthesizes; all reading/searching code, investigating, running tests and editing files "
        "goes to `hand` subagents from the start. Exception: plan/spec documents and review of "
        "hand diffs stay with the brain. "
        f"{_parallel_rule(config)} {_bug_rule(config)} "
        "Use the brief template loaded at session start; copy project rules verbatim into "
        "MANDATORY RULES."
    )


def subagent_start_text(config: ProjectConfig, inline_rules: bool = True) -> str:
    return (
        "PARALLEL-SUBAGENTS HAND CONTEXT: you are a hand. Follow the brief; no WRITE SCOPE means read-only. "
        "Do not review, commit, push or spawn agents.\n" + _project_block(config, inline_rules)
    )


def _read_event() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _agent_type(event: dict) -> str:
    for key in AGENT_TYPE_KEYS:
        value = event.get(key)
        if value:
            return str(value).strip().lower()
    return ""


TEXT_BUILDERS = {
    Event.SESSION_START: session_start_text,
    Event.USER_PROMPT: user_prompt_text,
    Event.SUBAGENT_START: subagent_start_text,
}


def _should_skip(kind: Event, agent_type: str) -> bool:
    if kind is Event.SUBAGENT_START:
        # Inject hand rules into hands; an unknown role still gets them (fail-safe, since the
        # stdin key naming the role is unverified), a known non-hand role does not.
        return bool(agent_type) and agent_type != HAND_AGENT_TYPE
    # A hand's own turns must not receive brain routing policy.
    return agent_type == HAND_AGENT_TYPE


def build_context(kind: Event, event: dict) -> Optional[str]:
    if _should_skip(kind, _agent_type(event)):
        return None
    config = load_project_config(Path(event.get("cwd") or Path.cwd()))
    builder = TEXT_BUILDERS[kind]
    text = builder(config)
    if len(text) > CONTEXT_LIMITS[kind]:
        text = builder(config, inline_rules=False)
    return text


def main(argv: List[str]) -> int:
    if len(argv) != 2 or argv[1] not in {e.value for e in Event}:
        print(f"usage: {argv[0]} {{{'|'.join(e.value for e in Event)}}}", file=sys.stderr)
        return 2
    kind = Event(argv[1])
    context = build_context(kind, _read_event())
    if context is None:
        print("{}")
        return 0
    output = {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT_NAMES[kind],
            "additionalContext": context,
        }
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
