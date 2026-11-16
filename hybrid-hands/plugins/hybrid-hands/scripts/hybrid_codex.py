#!/usr/bin/env python3
"""Read-only JSON bridge to the canonical hybrid-hands CLI."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

PROFILES = frozenset({"claude-mono", "gpt-mono", "hybrid"})
ROLES = frozenset({"code", "collect", "chrome"})
CORE_TIMEOUT_SECONDS = 20
DEFAULT_CORE = Path("app/claude-plugins/hybrid-hands/plugins/hybrid-hands/bin/hand-ext")


class AdapterError(ValueError):
    """A safe diagnostic that never includes untrusted core output."""


def validate_cwd(cwd: str | Path) -> Path:
    path = Path(cwd)
    if not path.is_absolute() or not path.is_dir():
        raise AdapterError("cwd must be an absolute directory")
    return path


def resolve_core(core_cli: str | Path | None = None) -> Path:
    candidate = core_cli if core_cli is not None else os.environ.get("HYBRID_HANDS_CORE_CLI")
    path = Path(candidate) if candidate is not None else Path.home() / DEFAULT_CORE
    if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
        raise AdapterError("core CLI must be an existing absolute executable")
    return path


def _request_tier(role: str | None, tier: int | None) -> int | None:
    if role not in ROLES:
        raise AdapterError("invalid role")
    if tier is not None and (type(tier) is not int or tier not in (1, 2)):
        raise AdapterError("invalid tier")
    if role == "code":
        if tier is not None:
            raise AdapterError("code does not accept a tier")
        return None
    return 1 if tier is None else tier


def _validate_payload(payload: Any, command: str, role: str | None,
                      expected_tier: int | None) -> dict[str, Any]:
    if (not isinstance(payload, dict) or not isinstance(payload.get("profile"), str)
            or payload["profile"] not in PROFILES):
        raise AdapterError("core returned an invalid profile")
    if command == "profile":
        if not isinstance(payload.get("roles"), dict):
            raise AdapterError("core returned invalid roles")
        return payload
    for field in ("role", "provider", "account", "model", "effort", "backend", "native_reason"):
        value = payload.get(field)
        if not isinstance(value, str) or (field != "native_reason" and not value.strip()):
            raise AdapterError("core returned invalid pick fields")
    for field in ("native", "guard_blocked"):
        if type(payload.get(field)) is not bool:
            raise AdapterError("core returned invalid pick booleans")
    tier = payload.get("tier")
    if "tier" not in payload or (tier is not None and (type(tier) is not int or tier not in (1, 2))):
        raise AdapterError("core returned an invalid tier")
    if payload["role"] != role or tier != expected_tier:
        raise AdapterError("core pick does not match request")
    if payload["guard_blocked"] and payload["native"]:
        raise AdapterError("core returned inconsistent guard state")
    return payload


def run_core(command: str, cwd: str | Path, core_cli: str | Path | None = None,
             role: str | None = None, tier: int | None = None) -> tuple[dict[str, Any], int]:
    if command not in ("profile", "pick"):
        raise AdapterError("unsupported command")
    if command == "profile" and (role is not None or tier is not None):
        raise AdapterError("profile does not accept role or tier")
    expected_tier = _request_tier(role, tier) if command == "pick" else None
    directory = validate_cwd(cwd)
    core = resolve_core(core_cli)
    argv = [str(core), command, "--cwd", str(directory), "--json"]
    if command == "pick":
        argv.extend(["--role", str(role)])
        if tier is not None:
            argv.extend(["--tier", str(tier)])
    try:
        result = subprocess.run(argv, cwd=directory, capture_output=True, text=True,
                                timeout=CORE_TIMEOUT_SECONDS, check=False)
    except subprocess.TimeoutExpired:
        raise AdapterError("core CLI timed out after 20 seconds") from None
    except (OSError, UnicodeError):
        raise AdapterError("core CLI could not be executed") from None
    try:
        payload = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise AdapterError("core CLI did not return valid JSON") from None
    return _validate_payload(payload, command, role, expected_tier), result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("profile", "pick"):
        sub = commands.add_parser(command)
        sub.add_argument("--cwd", required=True)
        sub.add_argument("--core-cli")
        if command == "pick":
            sub.add_argument("--role", choices=sorted(ROLES), required=True)
            sub.add_argument("--tier", type=int, choices=(1, 2))
    args = parser.parse_args(argv)
    try:
        payload, status = run_core(args.command, args.cwd, args.core_cli,
                                   getattr(args, "role", None), getattr(args, "tier", None))
    except AdapterError as exc:
        print(f"hybrid-codex: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False))
    return status


if __name__ == "__main__":
    sys.exit(main())
