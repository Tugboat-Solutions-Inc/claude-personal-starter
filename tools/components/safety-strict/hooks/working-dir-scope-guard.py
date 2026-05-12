#!/usr/bin/env python3
"""Block Write/Edit calls outside the user's working directory."""
import json
import sys
from pathlib import Path


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    tool = payload.get("tool_name") or payload.get("tool")
    if tool not in {"Write", "Edit"}:
        return 0

    manifest_path = Path("~/.claude/.claude-personal-starter.json").expanduser()
    if not manifest_path.exists():
        return 0
    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception:
        return 0
    working_dir = manifest.get("working_directory")
    if not working_dir:
        return 0
    working_dir = Path(working_dir).expanduser().resolve()

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
                f"Move the file there or ask the user to change the working directory."
            ),
        }))
        return 0


if __name__ == "__main__":
    sys.exit(main())
