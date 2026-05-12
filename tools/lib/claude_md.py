"""Managed-marker block parser and composer for ~/.claude/CLAUDE.md."""
import re


class ClaudeMdError(ValueError):
    pass


MARKER_PREFIX = "# >>> claude-personal-starter: "
MARKER_SUFFIX = "# <<< claude-personal-starter: "

_OPEN_RE = re.compile(r"^" + re.escape(MARKER_PREFIX) + r"(.+?)\s*$")
_CLOSE_RE = re.compile(r"^" + re.escape(MARKER_SUFFIX) + r"(.+?)\s*$")


def parse_blocks(text: str):
    """Return (blocks, freeform). blocks is id->content; freeform is everything else."""
    blocks = {}
    free_parts = []
    current_id = None
    current_lines = []
    for line in text.splitlines(keepends=False):
        open_m = _OPEN_RE.match(line)
        close_m = _CLOSE_RE.match(line)
        if open_m:
            if current_id is not None:
                raise ClaudeMdError(f"nested or unclosed block: opened {current_id!r}, then {open_m.group(1)!r}")
            current_id = open_m.group(1).strip()
            current_lines = []
        elif close_m:
            close_id = close_m.group(1).strip()
            if current_id is None:
                raise ClaudeMdError(f"close marker {close_id!r} with no open")
            if close_id != current_id:
                raise ClaudeMdError(f"mismatched markers: opened {current_id!r}, closed {close_id!r}")
            blocks[current_id] = "\n".join(current_lines)
            current_id = None
            current_lines = []
        elif current_id is not None:
            current_lines.append(line)
        else:
            free_parts.append(line)
    if current_id is not None:
        raise ClaudeMdError(f"unclosed block {current_id!r}")
    return blocks, "\n".join(free_parts)


def compose(blocks: dict, freeform: str) -> str:
    """Render a CLAUDE.md file from blocks (sorted by id) followed by freeform."""
    parts = []
    for cid in sorted(blocks.keys()):
        parts.append(f"{MARKER_PREFIX}{cid}")
        body = blocks[cid].rstrip("\n")
        if body:
            parts.append(body)
        parts.append(f"{MARKER_SUFFIX}{cid}")
        parts.append("")
    free = freeform.strip("\n")
    if free:
        parts.append(free)
        parts.append("")
    return "\n".join(parts)


def apply_changes(blocks: dict, freeform: str, add: dict, remove: set):
    """Return (new_blocks, new_freeform) with adds applied and removes dropped."""
    new_blocks = {k: v for k, v in blocks.items() if k not in remove}
    new_blocks.update(add)
    return new_blocks, freeform
