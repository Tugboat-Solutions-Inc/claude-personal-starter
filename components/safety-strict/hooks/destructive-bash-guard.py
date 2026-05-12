#!/usr/bin/env python3
"""Block destructive bash commands at PreToolUse."""
import json
import re
import sys


DESTRUCTIVE_PATTERNS = [
    (re.compile(r"\brm\s+-[rRf]+\s+/"), "rm -rf against /"),
    (re.compile(r"\brm\s+-[rRf]+\s+~(?!/Cases|/Work)"), "rm -rf against ~"),
    (re.compile(r"\bsudo\b"), "sudo"),
    (re.compile(r"\bgit\s+push\s+(-f|--force)"), "git force-push"),
    (re.compile(r"\bgit\s+reset\s+--hard"), "git reset --hard"),
    (re.compile(r"\bdefaults\s+write\b"), "defaults write"),
    (re.compile(r"\blaunchctl\b"), "launchctl"),
    (re.compile(r"\bdiskutil\b"), "diskutil"),
    (re.compile(r"\bsecurity\s+(add|delete|set)"), "security add/delete/set"),
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    tool = payload.get("tool_name") or payload.get("tool")
    if tool != "Bash":
        return 0
    cmd = (payload.get("tool_input") or {}).get("command", "")
    for pat, label in DESTRUCTIVE_PATTERNS:
        if pat.search(cmd):
            print(json.dumps({
                "continue": False,
                "stopReason": f"destructive-bash-guard blocked: {label}. Ask the user to run this manually.",
            }))
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
