#!/usr/bin/env python3
"""Block Write/Edit calls outside the user's working directory.

The /setup skill substitutes <<WORKING_DIR>> below with an absolute path before
copying this file into ~/.claude/hooks/.
"""
import json
import sys
from pathlib import Path


WORKING_DIR = "<<WORKING_DIR>>"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    tool = payload.get("tool_name") or payload.get("tool")
    if tool not in {"Write", "Edit"}:
        return 0

    if WORKING_DIR.startswith("<<"):
        # Placeholder never substituted — be permissive rather than break the user.
        return 0

    working_dir = Path(WORKING_DIR).expanduser().resolve()
    file_path = (payload.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        return 0
    try:
        target = Path(file_path).expanduser().resolve()
    except Exception:
        return 0
    try:
        target.relative_to(working_dir)
        return 0
    except ValueError:
        print(json.dumps({
            "continue": False,
            "stopReason": (
                f"working-dir-scope-guard blocked: {file_path} is outside {working_dir}. "
                f"Move the file there or re-run /setup to change the working directory."
            ),
        }))
        return 0


if __name__ == "__main__":
    sys.exit(main())
