#!/usr/bin/env python3
"""Copy the parallel-subagents `hand` agent definition to a Codex agents directory.

Codex discovers custom agents from ~/.codex/agents/ (personal) or <repo>/.codex/agents/ (project);
plugin manifests have no documented field for bundling agents, so this step is manual.

  python3 install_hand.py                  # -> ~/.codex/agents/hand.toml
  python3 install_hand.py --project DIR    # -> DIR/.codex/agents/hand.toml
  python3 install_hand.py --force          # overwrite a different existing hand.toml
  python3 install_hand.py --dry-run        # print the destination only
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

AGENT_FILE_NAME = "hand.toml"
SOURCE = Path(__file__).resolve().parents[1] / "agents" / AGENT_FILE_NAME
EXIT_CONFLICT = 3


def destination(project: Path | None) -> Path:
    base = project / ".codex" if project else Path.home() / ".codex"
    return base / "agents" / AGENT_FILE_NAME


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=Path, help="install into <project>/.codex/agents instead of ~/.codex/agents")
    parser.add_argument("--force", action="store_true", help="overwrite a differing existing file")
    parser.add_argument("--dry-run", action="store_true", help="print the destination without writing")
    args = parser.parse_args()
    target = destination(args.project)
    if args.dry_run:
        print(target)
        return 0
    if target.exists() and target.read_bytes() != SOURCE.read_bytes() and not args.force:
        print(f"refusing to overwrite differing {target}; re-run with --force", file=sys.stderr)
        return EXIT_CONFLICT
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, target)
    print(f"installed {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
