#!/usr/bin/env python3
"""Load the packaged workflow into a Codex root startup/resume hook."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = PLUGIN_ROOT / "skills" / "hybrid-hands" / "SKILL.md"
START_SOURCES = frozenset({"startup", "resume"})
AGENT_KEYS = ("agent_type", "agent_name", "subagent_type", "agent_id")


def build_output(event: Any, skill_path: Path = SKILL_PATH) -> dict[str, Any]:
    """Ignore invalid/non-root events; never block a session on a missing skill."""
    if not isinstance(event, dict):
        return {}
    if event.get("hook_event_name") != "SessionStart":
        return {}
    source = event.get("source")
    if not isinstance(source, str) or source not in START_SOURCES:
        return {}
    # Codex 0.169 dispatches SubagentStart separately. Also guard explicit role
    # metadata supplied by adapters; do not inject brain policy into a hand.
    if any(event.get(key) for key in AGENT_KEYS):
        return {}
    try:
        skill = skill_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"hybrid-hands: cannot load packaged skill ({type(error).__name__})", file=sys.stderr)
        return {}
    context = (
        f"Hybrid Hands startup skill loaded from {skill_path.resolve()}.\n"
        "Resolve relative skill links against this path. Apply this workflow when "
        "delegating; it does not authorize delegation or runtime changes by itself.\n\n"
        + skill
    )
    return {"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": context,
    }}


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        event = None
    print(json.dumps(build_output(event), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
