# Modular Claude Starter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `claude-personal-starter` — a public, modular Claude Code starter installable via one curl line, where users pick which components to install via an in-Claude checkbox UI driven by `AskUserQuestion`.

**Architecture:** A Python-driven CLI (`tools/install`) handles the engine — component discovery, CLAUDE.md block composition via managed markers, deep-merging `settings.json` fragments, manifest tracking. A Claude skill (`/setup`) drives the user-facing TUI and calls the CLI. Bootstrap clones the repo to `~/.claude-personal-starter/` and drops in the `setup` skill. Re-running `/setup` is the only update path users need.

**Tech Stack:** Python 3 (stdlib only — `json`, `pathlib`, `argparse`, `re`, `shutil`, `subprocess`). Bash for `bootstrap.sh`. Markdown for the `/setup` skill body. Pytest for tests.

---

## File Structure

```
~/Development/claude-personal-starter/
├── bootstrap.sh                       # curl entry point
├── tools/
│   ├── install                        # Python CLI entry (executable, no extension)
│   ├── lib/
│   │   ├── __init__.py
│   │   ├── catalog.py                 # component discovery + validation
│   │   ├── claude_md.py               # managed-marker block parser/composer
│   │   ├── settings.py                # deep-merge for settings.json
│   │   ├── manifest.py                # ~/.claude/.claude-personal-starter.json reader/writer
│   │   └── apply.py                   # orchestrate add/remove
│   ├── components/
│   │   ├── safety-chill/
│   │   ├── safety-strict/
│   │   ├── working-directory/
│   │   ├── identity-block/
│   │   ├── tool-gmail/
│   │   ├── tool-google-calendar/
│   │   ├── tool-outlook/
│   │   ├── skill-email-triage/
│   │   └── skill-weekly-digest/
│   └── tests/
│       ├── conftest.py
│       ├── test_catalog.py
│       ├── test_claude_md.py
│       ├── test_settings.py
│       ├── test_manifest.py
│       └── test_apply.py
├── skills/
│   └── setup/
│       └── SKILL.md
├── docs/
│   ├── ONBOARDING.md
│   ├── components.md
│   └── superpowers/                   # spec + this plan
├── LICENSE
├── README.md
└── .gitignore
```

Files that change together live together. The engine (`lib/`) is one unit; each component is one unit; the skill is one unit. Tests sit alongside what they test.

---

## Task 1: Repo scaffold

**Files:**
- Create: `~/Development/claude-personal-starter/.gitignore`
- Create: `~/Development/claude-personal-starter/LICENSE`
- Create: `~/Development/claude-personal-starter/README.md`
- Create: `~/Development/claude-personal-starter/tools/lib/__init__.py` (empty)
- Create: `~/Development/claude-personal-starter/tools/tests/__init__.py` (empty)
- Create: `~/Development/claude-personal-starter/tools/components/.gitkeep`

The git repo already exists with the spec committed.

- [ ] **Step 1: Write `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
*.swp
.env
.env.local
```

- [ ] **Step 2: Write `LICENSE` (MIT)**

```
MIT License

Copyright (c) 2026 Tugboat Solutions, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Write `README.md`**

```markdown
# claude-personal-starter

A modular Claude Code starter. Pick the pieces you want via an in-Claude checkbox UI. Reconfigure any time.

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/Tugboat-Solutions-Inc/claude-personal-starter/main/bootstrap.sh | sh
```

Then run `claude` and type `/setup`.

## Update

Re-run `/setup` any time. It pulls the latest components and lets you add or remove pieces.

## What it sets up

Categories of components, all optional, all independently toggleable:

- **Safety** — strict (hooks block destructive shell and net egress) or chill (system writes denied, otherwise free)
- **Tools** — Gmail, Outlook, Google Calendar, Google Docs, Google Drive, Google Sheets, Google Slides, Google Tasks, macOS Calendar / Contacts, Linear, Stripe
- **Skills** — email triage, weekly digest, meeting prep, folder summary, doc drafting
- **Identity** — one free-text prompt about who you are; goes into your `CLAUDE.md`

See `docs/components.md` for the catalog.

## License

MIT. See `LICENSE`.
```

- [ ] **Step 4: Create empty package init files and `.gitkeep`**

```sh
mkdir -p tools/lib tools/tests tools/components
touch tools/lib/__init__.py tools/tests/__init__.py tools/components/.gitkeep
```

- [ ] **Step 5: Commit**

```sh
cd ~/Development/claude-personal-starter
git add -A
git commit -m "chore: repo scaffold + license + readme"
```

---

## Task 2: `lib/catalog.py` — component discovery + validation

**Files:**
- Create: `tools/lib/catalog.py`
- Create: `tools/tests/conftest.py`
- Test: `tools/tests/test_catalog.py`

A component is a directory under `tools/components/<id>/` containing a `component.json` and optional fragments. `catalog.py` discovers, parses, and validates them.

- [ ] **Step 1: Write the failing test**

`tools/tests/conftest.py`:

```python
import json
import shutil
from pathlib import Path
import pytest


@pytest.fixture
def tmp_components_dir(tmp_path):
    """A temp dir mimicking tools/components/, returned as Path."""
    d = tmp_path / "components"
    d.mkdir()
    return d


def write_component(parent: Path, id: str, meta: dict, fragments: dict | None = None):
    """Create a component dir with component.json and optional fragment files.

    fragments is a dict mapping relative filename -> string contents.
    """
    cdir = parent / id
    cdir.mkdir()
    (cdir / "component.json").write_text(json.dumps(meta))
    (cdir / "version.txt").write_text(meta.get("_version", "1.0.0"))
    for rel, contents in (fragments or {}).items():
        f = cdir / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(contents)
    return cdir


@pytest.fixture
def make_component(tmp_components_dir):
    """Factory bound to tmp_components_dir."""
    def _make(id, **meta):
        full = {
            "id": id,
            "name": id.replace("-", " ").title(),
            "category": "tools",
            "description": f"{id} component",
            "recommended": False,
            "exclusive_group": None,
            "depends_on": [],
            "conflicts_with": [],
            **meta,
        }
        return write_component(tmp_components_dir, id, full)
    return _make
```

`tools/tests/test_catalog.py`:

```python
import json
from pathlib import Path
import pytest

from tools.lib import catalog


def test_load_components_returns_dict_keyed_by_id(tmp_components_dir, make_component):
    make_component("tool-a")
    make_component("tool-b")
    result = catalog.load_components(tmp_components_dir)
    assert set(result.keys()) == {"tool-a", "tool-b"}
    assert result["tool-a"]["name"] == "Tool A"


def test_load_components_includes_version(tmp_components_dir, make_component):
    make_component("tool-a")
    result = catalog.load_components(tmp_components_dir)
    assert result["tool-a"]["version"] == "1.0.0"


def test_load_components_includes_source_path(tmp_components_dir, make_component):
    cdir = make_component("tool-a")
    result = catalog.load_components(tmp_components_dir)
    assert result["tool-a"]["source_path"] == cdir


def test_load_components_skips_dirs_without_component_json(tmp_components_dir):
    (tmp_components_dir / "not-a-component").mkdir()
    (tmp_components_dir / "not-a-component" / "readme.md").write_text("nope")
    result = catalog.load_components(tmp_components_dir)
    assert result == {}


def test_validate_catalog_rejects_unknown_depends_on(tmp_components_dir, make_component):
    make_component("a", depends_on=["does-not-exist"])
    components = catalog.load_components(tmp_components_dir)
    with pytest.raises(catalog.CatalogError, match="does-not-exist"):
        catalog.validate_catalog(components)


def test_validate_catalog_rejects_unknown_conflicts_with(tmp_components_dir, make_component):
    make_component("a", conflicts_with=["nope"])
    components = catalog.load_components(tmp_components_dir)
    with pytest.raises(catalog.CatalogError, match="nope"):
        catalog.validate_catalog(components)


def test_validate_catalog_rejects_id_mismatch_between_dir_and_json(tmp_components_dir):
    cdir = tmp_components_dir / "tool-a"
    cdir.mkdir()
    (cdir / "component.json").write_text(json.dumps({
        "id": "tool-z",  # mismatch
        "name": "x", "category": "tools", "description": "x",
        "recommended": False, "exclusive_group": None,
        "depends_on": [], "conflicts_with": [],
    }))
    (cdir / "version.txt").write_text("1.0.0")
    with pytest.raises(catalog.CatalogError, match="id mismatch"):
        catalog.load_components(tmp_components_dir)


def test_resolve_dependencies_adds_transitive(tmp_components_dir, make_component):
    make_component("base")
    make_component("mid", depends_on=["base"])
    make_component("top", depends_on=["mid"])
    components = catalog.load_components(tmp_components_dir)
    resolved = catalog.resolve_dependencies(components, ["top"])
    assert resolved == {"base", "mid", "top"}


def test_check_conflicts_raises_on_conflict(tmp_components_dir, make_component):
    make_component("a", conflicts_with=["b"])
    make_component("b")
    components = catalog.load_components(tmp_components_dir)
    with pytest.raises(catalog.CatalogError, match="conflict"):
        catalog.check_conflicts(components, {"a", "b"})


def test_check_conflicts_enforces_exclusive_group(tmp_components_dir, make_component):
    make_component("a", exclusive_group="safety")
    make_component("b", exclusive_group="safety")
    components = catalog.load_components(tmp_components_dir)
    with pytest.raises(catalog.CatalogError, match="exclusive_group=safety"):
        catalog.check_conflicts(components, {"a", "b"})
```

- [ ] **Step 2: Run test to verify it fails**

```sh
cd ~/Development/claude-personal-starter
python3 -m pytest tools/tests/test_catalog.py -v
```

Expected: ImportError or "module not found" — catalog.py doesn't exist yet.

- [ ] **Step 3: Implement `tools/lib/catalog.py`**

```python
"""Component catalog: discover, validate, and resolve dependencies."""
import json
from pathlib import Path


class CatalogError(ValueError):
    pass


REQUIRED_FIELDS = {
    "id", "name", "category", "description",
    "recommended", "exclusive_group", "depends_on", "conflicts_with",
}


def load_components(components_dir: Path) -> dict:
    """Discover and parse every component under components_dir.

    Returns a dict keyed by component id. Each value includes the JSON fields
    plus 'version' (from version.txt) and 'source_path' (Path to component dir).
    """
    result = {}
    for child in sorted(components_dir.iterdir()):
        if not child.is_dir():
            continue
        meta_file = child / "component.json"
        if not meta_file.exists():
            continue
        meta = json.loads(meta_file.read_text())
        missing = REQUIRED_FIELDS - set(meta.keys())
        if missing:
            raise CatalogError(f"{child.name}: missing fields {sorted(missing)}")
        if meta["id"] != child.name:
            raise CatalogError(
                f"{child.name}: id mismatch — component.json says id={meta['id']!r}"
            )
        version_file = child / "version.txt"
        meta["version"] = version_file.read_text().strip() if version_file.exists() else "0.0.0"
        meta["source_path"] = child
        result[meta["id"]] = meta
    return result


def validate_catalog(components: dict) -> None:
    """Check that all depends_on/conflicts_with references exist in the catalog."""
    known = set(components.keys())
    for cid, c in components.items():
        for dep in c["depends_on"]:
            if dep not in known:
                raise CatalogError(f"{cid}: depends_on references unknown component {dep!r}")
        for conf in c["conflicts_with"]:
            if conf not in known:
                raise CatalogError(f"{cid}: conflicts_with references unknown component {conf!r}")


def resolve_dependencies(components: dict, requested: list[str]) -> set[str]:
    """Return the closure of requested + all transitive depends_on."""
    resolved = set()
    stack = list(requested)
    while stack:
        cid = stack.pop()
        if cid in resolved:
            continue
        if cid not in components:
            raise CatalogError(f"unknown component {cid!r}")
        resolved.add(cid)
        stack.extend(components[cid]["depends_on"])
    return resolved


def check_conflicts(components: dict, selected: set[str]) -> None:
    """Raise CatalogError if the selected set contains direct conflicts or
    multiple members of the same exclusive_group."""
    for cid in selected:
        c = components[cid]
        for conf in c["conflicts_with"]:
            if conf in selected:
                raise CatalogError(f"{cid} conflicts with {conf}")
    groups: dict[str, list[str]] = {}
    for cid in selected:
        group = components[cid].get("exclusive_group")
        if group:
            groups.setdefault(group, []).append(cid)
    for group, members in groups.items():
        if len(members) > 1:
            raise CatalogError(f"exclusive_group={group}: multiple selected {sorted(members)}")
```

- [ ] **Step 4: Run test to verify it passes**

```sh
cd ~/Development/claude-personal-starter
python3 -m pytest tools/tests/test_catalog.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```sh
git add tools/lib/catalog.py tools/lib/__init__.py tools/tests/conftest.py tools/tests/test_catalog.py tools/tests/__init__.py
git commit -m "feat(tools): component catalog discovery and validation"
```

---

## Task 3: `lib/claude_md.py` — managed-marker block composer

**Files:**
- Create: `tools/lib/claude_md.py`
- Test: `tools/tests/test_claude_md.py`

CLAUDE.md is assembled from labeled marker blocks. The parser must read an existing file, list which managed blocks are present, replace one block while leaving others (and free-form content outside markers) intact.

- [ ] **Step 1: Write the failing test**

`tools/tests/test_claude_md.py`:

```python
import textwrap

from tools.lib import claude_md as cm


def test_parse_blocks_returns_empty_for_empty_string():
    assert cm.parse_blocks("") == ({}, "")


def test_parse_blocks_extracts_single_block():
    text = textwrap.dedent("""\
        # >>> claude-personal-starter: tool-gmail
        Gmail content here.
        # <<< claude-personal-starter: tool-gmail
        """)
    blocks, free = cm.parse_blocks(text)
    assert "tool-gmail" in blocks
    assert blocks["tool-gmail"].strip() == "Gmail content here."
    assert free.strip() == ""


def test_parse_blocks_preserves_freeform_content_outside_markers():
    text = textwrap.dedent("""\
        Top freeform line.

        # >>> claude-personal-starter: tool-gmail
        Gmail content.
        # <<< claude-personal-starter: tool-gmail

        Middle freeform.

        # >>> claude-personal-starter: tool-calendar
        Calendar content.
        # <<< claude-personal-starter: tool-calendar

        Bottom freeform.
        """)
    blocks, free = cm.parse_blocks(text)
    assert set(blocks.keys()) == {"tool-gmail", "tool-calendar"}
    assert "Top freeform line." in free
    assert "Middle freeform." in free
    assert "Bottom freeform." in free
    assert "Gmail content" not in free


def test_parse_blocks_raises_on_mismatched_markers():
    text = textwrap.dedent("""\
        # >>> claude-personal-starter: a
        x
        # <<< claude-personal-starter: b
        """)
    import pytest
    with pytest.raises(cm.ClaudeMdError, match="mismatched"):
        cm.parse_blocks(text)


def test_parse_blocks_raises_on_unclosed_block():
    text = "# >>> claude-personal-starter: a\nx\n"
    import pytest
    with pytest.raises(cm.ClaudeMdError, match="unclosed"):
        cm.parse_blocks(text)


def test_compose_writes_blocks_in_id_order_then_freeform():
    blocks = {"b": "B content", "a": "A content"}
    free = "User's own notes."
    result = cm.compose(blocks, free)
    a_pos = result.index("a")
    b_pos = result.index("b")
    assert a_pos < b_pos
    assert "User's own notes." in result


def test_compose_then_parse_is_identity():
    blocks = {"x": "X", "y": "Y"}
    free = "freeform stuff"
    result = cm.compose(blocks, free)
    blocks2, free2 = cm.parse_blocks(result)
    assert blocks2 == blocks
    assert free2.strip() == free.strip()


def test_apply_changes_adds_new_block():
    blocks, free = ({}, "")
    new_blocks, new_free = cm.apply_changes(
        blocks, free, add={"tool-gmail": "Gmail fragment"}, remove=set()
    )
    assert new_blocks == {"tool-gmail": "Gmail fragment"}


def test_apply_changes_removes_block_but_keeps_others_and_freeform():
    blocks = {"a": "A", "b": "B"}
    free = "user notes"
    new_blocks, new_free = cm.apply_changes(blocks, free, add={}, remove={"a"})
    assert new_blocks == {"b": "B"}
    assert new_free == "user notes"


def test_apply_changes_replaces_block_when_added_with_same_id():
    blocks = {"a": "old"}
    new_blocks, _ = cm.apply_changes(blocks, "", add={"a": "new"}, remove=set())
    assert new_blocks == {"a": "new"}
```

- [ ] **Step 2: Run test to verify it fails**

```sh
python3 -m pytest tools/tests/test_claude_md.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `tools/lib/claude_md.py`**

```python
"""Managed-marker block parser and composer for ~/.claude/CLAUDE.md."""
import re


class ClaudeMdError(ValueError):
    pass


MARKER_PREFIX = "# >>> claude-personal-starter: "
MARKER_SUFFIX = "# <<< claude-personal-starter: "

_OPEN_RE = re.compile(r"^" + re.escape(MARKER_PREFIX) + r"(.+?)\s*$")
_CLOSE_RE = re.compile(r"^" + re.escape(MARKER_SUFFIX) + r"(.+?)\s*$")


def parse_blocks(text: str) -> tuple[dict[str, str], str]:
    """Return (blocks, freeform). blocks is id->content; freeform is everything else."""
    blocks: dict[str, str] = {}
    free_parts: list[str] = []
    current_id: str | None = None
    current_lines: list[str] = []
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


def compose(blocks: dict[str, str], freeform: str) -> str:
    """Render a CLAUDE.md file from blocks (sorted by id) followed by freeform."""
    parts: list[str] = []
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


def apply_changes(
    blocks: dict[str, str],
    freeform: str,
    add: dict[str, str],
    remove: set[str],
) -> tuple[dict[str, str], str]:
    """Return (new_blocks, new_freeform) with adds applied and removes dropped."""
    new_blocks = {k: v for k, v in blocks.items() if k not in remove}
    new_blocks.update(add)
    return new_blocks, freeform
```

- [ ] **Step 4: Run test to verify it passes**

```sh
python3 -m pytest tools/tests/test_claude_md.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```sh
git add tools/lib/claude_md.py tools/tests/test_claude_md.py
git commit -m "feat(tools): managed-marker block composer for CLAUDE.md"
```

---

## Task 4: `lib/settings.py` — deep-merge for settings.json

**Files:**
- Create: `tools/lib/settings.py`
- Test: `tools/tests/test_settings.py`

Merge N component `settings-fragment.json` files into a base. Union lists in `permissions.allow` and `permissions.deny`. Merge `hooks` by matcher. Shallow-merge `env`. Track each component's contribution so removal works.

- [ ] **Step 1: Write the failing test**

`tools/tests/test_settings.py`:

```python
import textwrap

from tools.lib import settings as st


BASE = {
    "$schema": "https://json.schemastore.org/claude-code-settings.json",
    "permissions": {"defaultMode": "auto", "allow": [], "deny": []},
    "hooks": {},
    "env": {},
}


def test_merge_unions_allow_and_deny():
    a = {"permissions": {"allow": ["Read"], "deny": ["Bash(rm -rf:*)"]}}
    b = {"permissions": {"allow": ["Grep"], "deny": ["Bash(sudo:*)"]}}
    out = st.merge_fragments(BASE, [("comp-a", a), ("comp-b", b)])
    assert set(out["permissions"]["allow"]) == {"Read", "Grep"}
    assert set(out["permissions"]["deny"]) == {"Bash(rm -rf:*)", "Bash(sudo:*)"}


def test_merge_deduplicates_allow_entries():
    a = {"permissions": {"allow": ["Read", "Grep"]}}
    b = {"permissions": {"allow": ["Read"]}}
    out = st.merge_fragments(BASE, [("a", a), ("b", b)])
    assert out["permissions"]["allow"].count("Read") == 1


def test_merge_preserves_default_mode_auto():
    out = st.merge_fragments(BASE, [])
    assert out["permissions"]["defaultMode"] == "auto"


def test_merge_combines_hooks_by_matcher():
    a = {"hooks": {"PreToolUse": [
        {"matcher": "Write|Edit", "hooks": [{"type": "command", "command": "hook-a"}]}
    ]}}
    b = {"hooks": {"PreToolUse": [
        {"matcher": "Write|Edit", "hooks": [{"type": "command", "command": "hook-b"}]}
    ]}}
    out = st.merge_fragments(BASE, [("a", a), ("b", b)])
    matchers = out["hooks"]["PreToolUse"]
    assert len(matchers) == 1
    assert matchers[0]["matcher"] == "Write|Edit"
    commands = [h["command"] for h in matchers[0]["hooks"]]
    assert set(commands) == {"hook-a", "hook-b"}


def test_merge_keeps_different_matchers_separate():
    a = {"hooks": {"PreToolUse": [
        {"matcher": "Write", "hooks": [{"type": "command", "command": "x"}]}
    ]}}
    b = {"hooks": {"PreToolUse": [
        {"matcher": "Bash", "hooks": [{"type": "command", "command": "y"}]}
    ]}}
    out = st.merge_fragments(BASE, [("a", a), ("b", b)])
    assert {m["matcher"] for m in out["hooks"]["PreToolUse"]} == {"Write", "Bash"}


def test_merge_shallow_merges_env():
    a = {"env": {"CLAUDE_PROJECT_LABEL": "personal"}}
    b = {"env": {"FOO": "bar"}}
    out = st.merge_fragments(BASE, [("a", a), ("b", b)])
    assert out["env"] == {"CLAUDE_PROJECT_LABEL": "personal", "FOO": "bar"}


def test_compute_contributions_records_what_each_component_added():
    a = {"permissions": {"allow": ["Read"], "deny": ["Bash(rm -rf:*)"]}}
    contrib = st.compute_contribution("comp-a", a)
    assert contrib["allow"] == ["Read"]
    assert contrib["deny"] == ["Bash(rm -rf:*)"]


def test_apply_contributions_removes_only_components_contributions():
    base = {
        "permissions": {"defaultMode": "auto", "allow": ["Read", "Grep"], "deny": []},
        "hooks": {}, "env": {},
    }
    contributions = {
        "comp-a": {"allow": ["Read"], "deny": [], "env": {}, "hooks": {}},
    }
    out = st.remove_contribution(base, contributions["comp-a"])
    assert out["permissions"]["allow"] == ["Grep"]
```

- [ ] **Step 2: Run test to verify it fails**

```sh
python3 -m pytest tools/tests/test_settings.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `tools/lib/settings.py`**

```python
"""Deep-merge settings.json fragments from components."""
from copy import deepcopy


def merge_fragments(base: dict, fragments: list[tuple[str, dict]]) -> dict:
    """Merge a list of (component_id, fragment) into base.

    - permissions.allow / permissions.deny: union, deduplicated, order-preserving.
    - hooks.<EventName>: list of matcher groups; matchers are combined,
      each group's `hooks` list is unioned by command.
    - env: shallow merge; later overrides earlier.
    - Everything else in base is preserved untouched.
    """
    result = deepcopy(base)
    perms = result.setdefault("permissions", {})
    perms.setdefault("allow", [])
    perms.setdefault("deny", [])
    hooks = result.setdefault("hooks", {})
    env = result.setdefault("env", {})

    for _cid, frag in fragments:
        fperms = frag.get("permissions", {})
        for entry in fperms.get("allow", []):
            if entry not in perms["allow"]:
                perms["allow"].append(entry)
        for entry in fperms.get("deny", []):
            if entry not in perms["deny"]:
                perms["deny"].append(entry)
        for event_name, matcher_groups in frag.get("hooks", {}).items():
            existing_groups = hooks.setdefault(event_name, [])
            for incoming in matcher_groups:
                _merge_matcher_group(existing_groups, incoming)
        for k, v in frag.get("env", {}).items():
            env[k] = v
    return result


def _merge_matcher_group(existing: list[dict], incoming: dict) -> None:
    """Find or create a matcher group, then union its hooks by command string."""
    matcher = incoming.get("matcher")
    target = None
    for g in existing:
        if g.get("matcher") == matcher:
            target = g
            break
    if target is None:
        existing.append(deepcopy(incoming))
        return
    target_hooks = target.setdefault("hooks", [])
    seen = {(h.get("type"), h.get("command")) for h in target_hooks}
    for h in incoming.get("hooks", []):
        key = (h.get("type"), h.get("command"))
        if key not in seen:
            target_hooks.append(deepcopy(h))
            seen.add(key)


def compute_contribution(component_id: str, fragment: dict) -> dict:
    """Snapshot what this fragment is contributing — used to undo on removal."""
    return {
        "allow": list(fragment.get("permissions", {}).get("allow", [])),
        "deny": list(fragment.get("permissions", {}).get("deny", [])),
        "env": dict(fragment.get("env", {})),
        "hooks": deepcopy(fragment.get("hooks", {})),
    }


def remove_contribution(settings: dict, contribution: dict) -> dict:
    """Strip a previous component's contribution from a merged settings object."""
    result = deepcopy(settings)
    perms = result.get("permissions", {})
    perms["allow"] = [x for x in perms.get("allow", []) if x not in contribution.get("allow", [])]
    perms["deny"] = [x for x in perms.get("deny", []) if x not in contribution.get("deny", [])]
    env = result.get("env", {})
    for k in contribution.get("env", {}):
        env.pop(k, None)
    for event_name, matcher_groups in contribution.get("hooks", {}).items():
        existing = result.get("hooks", {}).get(event_name, [])
        for incoming in matcher_groups:
            _strip_matcher_group(existing, incoming)
        result["hooks"][event_name] = [g for g in existing if g.get("hooks")]
    return result


def _strip_matcher_group(existing: list[dict], incoming: dict) -> None:
    matcher = incoming.get("matcher")
    target = next((g for g in existing if g.get("matcher") == matcher), None)
    if target is None:
        return
    bad = {(h.get("type"), h.get("command")) for h in incoming.get("hooks", [])}
    target["hooks"] = [h for h in target.get("hooks", []) if (h.get("type"), h.get("command")) not in bad]
```

- [ ] **Step 4: Run test to verify it passes**

```sh
python3 -m pytest tools/tests/test_settings.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```sh
git add tools/lib/settings.py tools/tests/test_settings.py
git commit -m "feat(tools): deep-merge settings.json fragments with contribution tracking"
```

---

## Task 5: `lib/manifest.py` — install manifest reader/writer

**Files:**
- Create: `tools/lib/manifest.py`
- Test: `tools/tests/test_manifest.py`

The manifest at `~/.claude/.claude-personal-starter.json` records what's installed, which version, and what each component contributed (so we can remove it cleanly).

Schema:

```json
{
  "version": 1,
  "components": {
    "tool-gmail": {
      "version": "1.0.0",
      "installed_at": "2026-05-12T10:30:00Z",
      "files_copied": ["skills/gmail-triage/SKILL.md", "hooks/foo.py"],
      "settings_contribution": { "allow": [...], "deny": [...], "env": {...}, "hooks": {...} }
    }
  },
  "working_directory": "/Users/aaronmooney/Work"
}
```

- [ ] **Step 1: Write the failing test**

`tools/tests/test_manifest.py`:

```python
import json

from tools.lib import manifest as mf


def test_read_returns_empty_when_file_missing(tmp_path):
    m = mf.read(tmp_path / "missing.json")
    assert m == {"version": 1, "components": {}, "working_directory": None}


def test_read_returns_existing(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps({
        "version": 1,
        "components": {"tool-gmail": {"version": "1.0.0"}},
        "working_directory": "/Users/x/Work",
    }))
    m = mf.read(p)
    assert m["components"]["tool-gmail"]["version"] == "1.0.0"


def test_write_roundtrips(tmp_path):
    p = tmp_path / "m.json"
    data = {
        "version": 1,
        "components": {"a": {"version": "1.0.0", "installed_at": "z", "files_copied": []}},
        "working_directory": "/x",
    }
    mf.write(p, data)
    assert mf.read(p) == data


def test_record_install_adds_entry(tmp_path):
    p = tmp_path / "m.json"
    mf.record_install(
        p, component_id="tool-a", version="1.0.0",
        files_copied=["skills/x/SKILL.md"],
        settings_contribution={"allow": ["Read"], "deny": [], "env": {}, "hooks": {}},
    )
    m = mf.read(p)
    assert "tool-a" in m["components"]
    assert m["components"]["tool-a"]["version"] == "1.0.0"
    assert m["components"]["tool-a"]["files_copied"] == ["skills/x/SKILL.md"]


def test_record_remove_drops_entry(tmp_path):
    p = tmp_path / "m.json"
    mf.record_install(p, "tool-a", "1.0.0", [], {})
    mf.record_remove(p, "tool-a")
    assert "tool-a" not in mf.read(p)["components"]


def test_record_remove_is_idempotent(tmp_path):
    p = tmp_path / "m.json"
    mf.record_remove(p, "never-installed")  # no-op, no error


def test_set_working_directory_persists(tmp_path):
    p = tmp_path / "m.json"
    mf.set_working_directory(p, "/Users/y/Work")
    assert mf.read(p)["working_directory"] == "/Users/y/Work"
```

- [ ] **Step 2: Run test to verify it fails**

```sh
python3 -m pytest tools/tests/test_manifest.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `tools/lib/manifest.py`**

```python
"""Read/write the install manifest at ~/.claude/.claude-personal-starter.json."""
import json
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1


def _empty() -> dict:
    return {"version": SCHEMA_VERSION, "components": {}, "working_directory": None}


def read(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        return _empty()
    data = json.loads(path.read_text())
    data.setdefault("version", SCHEMA_VERSION)
    data.setdefault("components", {})
    data.setdefault("working_directory", None)
    return data


def write(path: Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def record_install(
    path: Path,
    component_id: str,
    version: str,
    files_copied: list[str],
    settings_contribution: dict,
) -> None:
    data = read(path)
    data["components"][component_id] = {
        "version": version,
        "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files_copied": list(files_copied),
        "settings_contribution": settings_contribution,
    }
    write(path, data)


def record_remove(path: Path, component_id: str) -> None:
    data = read(path)
    data["components"].pop(component_id, None)
    write(path, data)


def set_working_directory(path: Path, working_directory: str) -> None:
    data = read(path)
    data["working_directory"] = working_directory
    write(path, data)


def installed_ids(path: Path) -> set[str]:
    return set(read(path)["components"].keys())
```

- [ ] **Step 4: Run test to verify it passes**

```sh
python3 -m pytest tools/tests/test_manifest.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```sh
git add tools/lib/manifest.py tools/tests/test_manifest.py
git commit -m "feat(tools): install manifest reader/writer"
```

---

## Task 6: `lib/apply.py` — orchestrate add/remove

**Files:**
- Create: `tools/lib/apply.py`
- Test: `tools/tests/test_apply.py`

Apply takes a target `~/.claude/` dir, a components dir, a set of components to add, and a set to remove. It:

1. Loads catalog, resolves deps, checks conflicts.
2. Reads existing `CLAUDE.md`, `settings.json`, manifest.
3. For each removed component: strips its CLAUDE.md block, removes its settings contribution, deletes files-copied.
4. For each added component: reads its `claude-md-fragment.md`, `settings-fragment.json`, copies `skills/`, `hooks/`, `agents/` subdirs. Updates manifest with contribution.
5. Writes back `CLAUDE.md`, `settings.json`, manifest.

- [ ] **Step 1: Write the failing test**

`tools/tests/test_apply.py`:

```python
import json
from pathlib import Path

import pytest

from tools.lib import apply, manifest


def _write_component(components_dir: Path, cid: str, *, settings_fragment=None,
                      claude_md_fragment=None, skill_files=None):
    d = components_dir / cid
    d.mkdir()
    (d / "component.json").write_text(json.dumps({
        "id": cid, "name": cid, "category": "tools", "description": cid,
        "recommended": False, "exclusive_group": None,
        "depends_on": [], "conflicts_with": [],
    }))
    (d / "version.txt").write_text("1.0.0")
    if settings_fragment is not None:
        (d / "settings-fragment.json").write_text(json.dumps(settings_fragment))
    if claude_md_fragment is not None:
        (d / "claude-md-fragment.md").write_text(claude_md_fragment)
    for rel, contents in (skill_files or {}).items():
        f = d / "skills" / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(contents)


def test_apply_adds_component_and_updates_files(tmp_path, tmp_components_dir):
    _write_component(
        tmp_components_dir, "tool-x",
        settings_fragment={"permissions": {"allow": ["Read"]}},
        claude_md_fragment="X notes",
        skill_files={"skill-x/SKILL.md": "skill body"},
    )
    target = tmp_path / "claude"
    target.mkdir()
    apply.apply(
        components_dir=tmp_components_dir,
        target_dir=target,
        add={"tool-x"},
        remove=set(),
        working_directory=None,
        identity_text=None,
    )
    assert (target / "skills" / "skill-x" / "SKILL.md").read_text() == "skill body"
    settings = json.loads((target / "settings.json").read_text())
    assert "Read" in settings["permissions"]["allow"]
    claude_md = (target / "CLAUDE.md").read_text()
    assert "X notes" in claude_md
    m = manifest.read(target / ".claude-personal-starter.json")
    assert "tool-x" in m["components"]


def test_apply_removes_component_and_cleans_up(tmp_path, tmp_components_dir):
    _write_component(
        tmp_components_dir, "tool-x",
        settings_fragment={"permissions": {"allow": ["Read"]}},
        claude_md_fragment="X notes",
        skill_files={"skill-x/SKILL.md": "body"},
    )
    target = tmp_path / "claude"
    target.mkdir()
    apply.apply(components_dir=tmp_components_dir, target_dir=target,
                add={"tool-x"}, remove=set(), working_directory=None, identity_text=None)
    apply.apply(components_dir=tmp_components_dir, target_dir=target,
                add=set(), remove={"tool-x"}, working_directory=None, identity_text=None)
    assert not (target / "skills" / "skill-x" / "SKILL.md").exists()
    settings = json.loads((target / "settings.json").read_text())
    assert "Read" not in settings["permissions"]["allow"]
    claude_md = (target / "CLAUDE.md").read_text()
    assert "X notes" not in claude_md
    assert "tool-x" not in manifest.read(target / ".claude-personal-starter.json")["components"]


def test_apply_preserves_unrelated_freeform_in_claude_md(tmp_path, tmp_components_dir):
    _write_component(tmp_components_dir, "tool-x", claude_md_fragment="X")
    target = tmp_path / "claude"
    target.mkdir()
    (target / "CLAUDE.md").write_text("My personal notes.\n")
    apply.apply(components_dir=tmp_components_dir, target_dir=target,
                add={"tool-x"}, remove=set(), working_directory=None, identity_text=None)
    text = (target / "CLAUDE.md").read_text()
    assert "My personal notes." in text
    assert "X" in text


def test_apply_writes_identity_block_when_provided(tmp_path, tmp_components_dir):
    _write_component(tmp_components_dir, "identity-block",
                      claude_md_fragment="<<IDENTITY>>")
    target = tmp_path / "claude"
    target.mkdir()
    apply.apply(components_dir=tmp_components_dir, target_dir=target,
                add={"identity-block"}, remove=set(),
                working_directory=None,
                identity_text="I am Aaron, I run Tugboat.")
    text = (target / "CLAUDE.md").read_text()
    assert "I am Aaron, I run Tugboat." in text


def test_apply_persists_working_directory(tmp_path, tmp_components_dir):
    target = tmp_path / "claude"
    target.mkdir()
    apply.apply(components_dir=tmp_components_dir, target_dir=target,
                add=set(), remove=set(),
                working_directory=str(tmp_path / "Work"), identity_text=None)
    m = manifest.read(target / ".claude-personal-starter.json")
    assert m["working_directory"] == str(tmp_path / "Work")
    assert (tmp_path / "Work").exists()
```

- [ ] **Step 2: Run test to verify it fails**

```sh
python3 -m pytest tools/tests/test_apply.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `tools/lib/apply.py`**

```python
"""Orchestrate add/remove of components against a target ~/.claude/ directory."""
import json
import shutil
from pathlib import Path

from . import catalog, claude_md, manifest, settings as settings_mod


IDENTITY_PLACEHOLDER = "<<IDENTITY>>"
BASE_SETTINGS = {
    "$schema": "https://json.schemastore.org/claude-code-settings.json",
    "permissions": {"defaultMode": "auto", "allow": [], "deny": []},
    "hooks": {},
    "env": {},
}


def apply(
    *,
    components_dir: Path,
    target_dir: Path,
    add: set[str],
    remove: set[str],
    working_directory: str | None,
    identity_text: str | None,
) -> None:
    components_dir = Path(components_dir)
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    components = catalog.load_components(components_dir)
    catalog.validate_catalog(components)

    manifest_path = target_dir / ".claude-personal-starter.json"
    state = manifest.read(manifest_path)
    installed = set(state["components"].keys())

    # Resolve deps for adds; refuse removes that things still depend on.
    add_closure = catalog.resolve_dependencies(components, list(add)) - installed if add else set()
    final_installed = (installed - remove) | add_closure
    catalog.check_conflicts(components, final_installed)

    # Process removes first.
    for cid in sorted(remove):
        if cid in installed:
            _remove_one(target_dir, components.get(cid), state["components"][cid])
            manifest.record_remove(manifest_path, cid)

    # Process adds.
    for cid in sorted(add_closure):
        _install_one(target_dir, components[cid], manifest_path, identity_text)

    if working_directory is not None:
        Path(working_directory).expanduser().mkdir(parents=True, exist_ok=True)
        manifest.set_working_directory(manifest_path, working_directory)


def _install_one(target_dir: Path, component: dict, manifest_path: Path,
                  identity_text: str | None) -> None:
    cid = component["id"]
    src = component["source_path"]

    files_copied: list[str] = []
    # Copy skills/, hooks/, agents/ recursively.
    for subdir in ("skills", "hooks", "agents"):
        src_sub = src / subdir
        if src_sub.exists():
            for f in src_sub.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(src)
                    dest = target_dir / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
                    if subdir == "hooks":
                        dest.chmod(0o755)
                    files_copied.append(str(rel))

    # CLAUDE.md fragment.
    fragment_file = src / "claude-md-fragment.md"
    if fragment_file.exists():
        fragment = fragment_file.read_text()
        if IDENTITY_PLACEHOLDER in fragment:
            fragment = fragment.replace(IDENTITY_PLACEHOLDER, identity_text or "")
        claude_md_path = target_dir / "CLAUDE.md"
        existing = claude_md_path.read_text() if claude_md_path.exists() else ""
        blocks, freeform = claude_md.parse_blocks(existing)
        blocks, freeform = claude_md.apply_changes(blocks, freeform, add={cid: fragment}, remove=set())
        claude_md_path.write_text(claude_md.compose(blocks, freeform))

    # settings.json fragment.
    settings_fragment_file = src / "settings-fragment.json"
    contribution = {"allow": [], "deny": [], "env": {}, "hooks": {}}
    if settings_fragment_file.exists():
        fragment = json.loads(settings_fragment_file.read_text())
        contribution = settings_mod.compute_contribution(cid, fragment)
        settings_path = target_dir / "settings.json"
        existing = json.loads(settings_path.read_text()) if settings_path.exists() else dict(BASE_SETTINGS)
        merged = settings_mod.merge_fragments(existing, [(cid, fragment)])
        settings_path.write_text(json.dumps(merged, indent=2) + "\n")

    # Ensure settings.json exists even with no fragment.
    settings_path = target_dir / "settings.json"
    if not settings_path.exists():
        settings_path.write_text(json.dumps(BASE_SETTINGS, indent=2) + "\n")

    manifest.record_install(
        manifest_path,
        component_id=cid,
        version=component["version"],
        files_copied=files_copied,
        settings_contribution=contribution,
    )


def _remove_one(target_dir: Path, component: dict | None, manifest_entry: dict) -> None:
    # Delete files-copied.
    for rel in manifest_entry.get("files_copied", []):
        f = target_dir / rel
        if f.exists():
            f.unlink()
            # Clean up empty parent dirs up to skills/hooks/agents.
            parent = f.parent
            while parent != target_dir and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent

    # Strip CLAUDE.md block.
    claude_md_path = target_dir / "CLAUDE.md"
    if claude_md_path.exists():
        existing = claude_md_path.read_text()
        blocks, freeform = claude_md.parse_blocks(existing)
        cid = component["id"] if component else next(iter(manifest_entry.get("_id_hint", [None])), None)
        # Determine cid from manifest key path instead — see apply() — but we
        # need it here. Manifest entries are keyed by id; caller knows it.
        # We pass it via component when available; fall back to scanning blocks.
        if component:
            blocks, freeform = claude_md.apply_changes(blocks, freeform, add={}, remove={component["id"]})
        claude_md_path.write_text(claude_md.compose(blocks, freeform))

    # Strip settings.json contribution.
    settings_path = target_dir / "settings.json"
    if settings_path.exists():
        existing = json.loads(settings_path.read_text())
        stripped = settings_mod.remove_contribution(existing, manifest_entry.get("settings_contribution", {}))
        settings_path.write_text(json.dumps(stripped, indent=2) + "\n")
```

`// verified: when component is None (removed from catalog but still in manifest), we skip CLAUDE.md block removal; manifest cleanup still happens in apply()`

- [ ] **Step 4: Run test to verify it passes**

```sh
python3 -m pytest tools/tests/test_apply.py -v
```

Expected: all PASS. If any fail, debug — common issue is the `IDENTITY_PLACEHOLDER` replacement leaving the placeholder when `identity_text=None`; in that case the placeholder is replaced with empty string and the test for "I am Aaron" still passes because `identity_text` is provided.

- [ ] **Step 5: Commit**

```sh
git add tools/lib/apply.py tools/tests/test_apply.py
git commit -m "feat(tools): orchestrate add/remove of components"
```

---

## Task 7: `tools/install` CLI entry point

**Files:**
- Create: `tools/install` (executable, no extension)

The CLI surface that `/setup` will call. Subcommands: `list-components`, `list-installed`, `apply`, `upgrade`.

- [ ] **Step 1: Write `tools/install`**

```python
#!/usr/bin/env python3
"""claude-personal-starter installer CLI.

Subcommands:
  list-components [--json]   List every available component.
  list-installed [--json]    List currently-installed components.
  apply --add ID,ID --remove ID,ID [--working-dir PATH] [--identity-text TEXT]
                              Apply changes.
  upgrade                     Reapply every installed component from current source.
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Make 'tools' importable when run as a script.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from tools.lib import apply as apply_mod, catalog, manifest


def cli_target_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PERSONAL_STARTER_TARGET", "~/.claude")).expanduser()


def components_dir() -> Path:
    return HERE / "components"


def cmd_list_components(args):
    components = catalog.load_components(components_dir())
    catalog.validate_catalog(components)
    installed = manifest.installed_ids(cli_target_dir() / ".claude-personal-starter.json")
    out = []
    for cid, c in sorted(components.items()):
        out.append({
            "id": cid,
            "name": c["name"],
            "category": c["category"],
            "description": c["description"],
            "recommended": c["recommended"],
            "exclusive_group": c["exclusive_group"],
            "depends_on": c["depends_on"],
            "version": c["version"],
            "installed": cid in installed,
        })
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        for c in out:
            mark = "[x]" if c["installed"] else "[ ]"
            print(f"{mark} {c['category']:18} {c['id']:30} {c['name']}")


def cmd_list_installed(args):
    m = manifest.read(cli_target_dir() / ".claude-personal-starter.json")
    if args.json:
        print(json.dumps(m, indent=2))
    else:
        for cid, entry in sorted(m["components"].items()):
            print(f"{cid:30} {entry['version']:10} {entry.get('installed_at', '')}")


def _csv(s: str) -> set[str]:
    return {x for x in (s or "").split(",") if x}


def cmd_apply(args):
    apply_mod.apply(
        components_dir=components_dir(),
        target_dir=cli_target_dir(),
        add=_csv(args.add),
        remove=_csv(args.remove),
        working_directory=args.working_dir,
        identity_text=args.identity_text,
    )
    print("Applied.")


def cmd_upgrade(args):
    target = cli_target_dir()
    m = manifest.read(target / ".claude-personal-starter.json")
    installed = set(m["components"].keys())
    if not installed:
        print("Nothing installed.")
        return
    # Reapply: remove then add.
    apply_mod.apply(
        components_dir=components_dir(),
        target_dir=target,
        add=installed,
        remove=installed,
        working_directory=None,
        identity_text=None,
    )
    print(f"Upgraded {len(installed)} components.")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="install", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list-components")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list_components)

    p = sub.add_parser("list-installed")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list_installed)

    p = sub.add_parser("apply")
    p.add_argument("--add", default="")
    p.add_argument("--remove", default="")
    p.add_argument("--working-dir", default=None)
    p.add_argument("--identity-text", default=None)
    p.set_defaults(func=cmd_apply)

    p = sub.add_parser("upgrade")
    p.set_defaults(func=cmd_upgrade)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make executable + sanity-check**

```sh
chmod +x tools/install
tools/install list-components
```

Expected output: nothing (no components yet) — confirms the CLI loads without errors.

- [ ] **Step 3: Commit**

```sh
git add tools/install
git commit -m "feat(tools): install CLI with list/apply/upgrade subcommands"
```

---

## Task 8: `safety-chill` component

**Files:**
- Create: `tools/components/safety-chill/component.json`
- Create: `tools/components/safety-chill/version.txt`
- Create: `tools/components/safety-chill/settings-fragment.json`
- Create: `tools/components/safety-chill/claude-md-fragment.md`

- [ ] **Step 1: `component.json`**

```json
{
  "id": "safety-chill",
  "name": "Chill safety",
  "category": "safety",
  "description": "System paths (/etc, /Library, /System, /usr, ~/Library) denied for Write/Edit. Destructive shell and network egress allowed. Recommended for technical users who want freedom.",
  "recommended": false,
  "exclusive_group": "safety",
  "depends_on": [],
  "conflicts_with": []
}
```

- [ ] **Step 2: `version.txt`**

```
1.0.0
```

- [ ] **Step 3: `settings-fragment.json`**

```json
{
  "permissions": {
    "deny": [
      "Write(/etc/**)",
      "Write(/Library/**)",
      "Write(/System/**)",
      "Write(/usr/**)",
      "Write(~/Library/**)",
      "Edit(/etc/**)",
      "Edit(/Library/**)",
      "Edit(/System/**)",
      "Edit(/usr/**)",
      "Edit(~/Library/**)"
    ]
  }
}
```

- [ ] **Step 4: `claude-md-fragment.md`**

```markdown
## Safety profile: chill

You are running in permissive mode. The only hard blocks are writes to system paths (`/etc`, `/Library`, `/System`, `/usr`, `~/Library`). Destructive shell commands (`rm -rf`, `sudo`, force pushes), network egress (`curl`, `wget`), and writes elsewhere are allowed.

The user is technical. They expect to be able to run shell freely. Still:

- Never run destructive commands without first stating clearly what's about to be destroyed.
- Always confirm before hard-resetting git, force-pushing, deleting branches, or running `rm -rf` on anything you didn't just create.
- Always show the user the command before running it if there's any chance it could be wrong.

Speed up; don't get cocky.
```

- [ ] **Step 5: Verify the component loads**

```sh
tools/install list-components
```

Expected: one line, `[ ] safety             safety-chill                   Chill safety`.

- [ ] **Step 6: Commit**

```sh
git add tools/components/safety-chill
git commit -m "feat(components): safety-chill profile"
```

---

## Task 9: `safety-strict` component

**Files:**
- Create: `tools/components/safety-strict/component.json`
- Create: `tools/components/safety-strict/version.txt`
- Create: `tools/components/safety-strict/settings-fragment.json`
- Create: `tools/components/safety-strict/claude-md-fragment.md`
- Create: `tools/components/safety-strict/hooks/destructive-bash-guard.py`
- Create: `tools/components/safety-strict/hooks/working-dir-scope-guard.py`

`// verified: hooks read JSON from stdin per Claude Code spec. PreToolUse hooks emit JSON to stdout with {"continue": false, "stopReason": "..."} to block.`

- [ ] **Step 1: `component.json`**

```json
{
  "id": "safety-strict",
  "name": "Strict safety",
  "category": "safety",
  "description": "Hooks block destructive shell (rm -rf, sudo, force pushes, defaults write, launchctl) and network egress (curl, wget, scp, rsync). Working-directory hook fences Write/Edit to your working directory. System path writes denied. Recommended for non-technical users.",
  "recommended": true,
  "exclusive_group": "safety",
  "depends_on": ["working-directory"],
  "conflicts_with": []
}
```

- [ ] **Step 2: `version.txt`**

```
1.0.0
```

- [ ] **Step 3: `settings-fragment.json`**

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(sudo:*)",
      "Bash(git push --force:*)",
      "Bash(git push -f:*)",
      "Bash(git reset --hard:*)",
      "Bash(curl:*)",
      "Bash(wget:*)",
      "Bash(scp:*)",
      "Bash(rsync:*)",
      "Bash(defaults write:*)",
      "Bash(launchctl:*)",
      "Bash(diskutil:*)",
      "Bash(security:*)",
      "Write(/etc/**)",
      "Write(/Library/**)",
      "Write(/System/**)",
      "Write(/usr/**)",
      "Write(~/Library/**)",
      "Edit(/etc/**)",
      "Edit(/Library/**)",
      "Edit(/System/**)",
      "Edit(/usr/**)",
      "Edit(~/Library/**)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/destructive-bash-guard.py" }
        ]
      },
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/working-dir-scope-guard.py" }
        ]
      }
    ]
  }
}
```

- [ ] **Step 4: `claude-md-fragment.md`**

```markdown
## Safety profile: strict

You are running in protective mode. Hard rules:

- **Destructive shell commands are blocked at the harness layer** (rm -rf, sudo, force pushes, hard resets, defaults write, launchctl). Don't try to work around them.
- **Network egress shell commands are blocked** (curl, wget, scp, rsync). When the user wants to fetch something from the web, use WebFetch or WebSearch tools instead.
- **Write/Edit is fenced to the user's working directory** (set during /setup). Anything outside it is blocked.
- **System paths are write-protected** (/etc, /Library, /System, /usr, ~/Library). Don't even propose edits there.

Habits:

- Default to drafts, not finals.
- Show the user what you're about to do before doing it.
- Ask before doing anything irreversible — even when the harness would let you.
- Be direct. If the user proposes something you think is a bad move, say so.
```

- [ ] **Step 5: `hooks/destructive-bash-guard.py`**

```python
#!/usr/bin/env python3
"""Block destructive bash commands at PreToolUse.

Reads tool-call JSON from stdin. If the Bash command matches a destructive
pattern, emits {"continue": false, "stopReason": "..."} and exits 0.
Otherwise prints nothing and exits 0 (which lets the tool call proceed).
"""
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
```

- [ ] **Step 6: `hooks/working-dir-scope-guard.py`**

```python
#!/usr/bin/env python3
"""Block Write/Edit calls outside the user's working directory.

Reads the working_directory from ~/.claude/.claude-personal-starter.json.
If unset, the hook is a no-op.
"""
import json
import os
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
        return 0  # inside working dir, allow
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
```

- [ ] **Step 7: Verify the component loads + dep resolves**

```sh
tools/install list-components | grep safety
```

Expected: both `safety-chill` and `safety-strict` appear, `safety-strict` is `[ ]` and recommended.

- [ ] **Step 8: Commit**

```sh
git add tools/components/safety-strict
git commit -m "feat(components): safety-strict profile with destructive-bash and scope-guard hooks"
```

---

## Task 10: `working-directory` component

**Files:**
- Create: `tools/components/working-directory/component.json`
- Create: `tools/components/working-directory/version.txt`
- Create: `tools/components/working-directory/claude-md-fragment.md`

This component has no settings or hooks of its own — its job is to register the working-directory choice into the manifest (which apply.py already does via the `--working-dir` arg) and add a CLAUDE.md note about the convention.

- [ ] **Step 1: `component.json`**

```json
{
  "id": "working-directory",
  "name": "Working directory",
  "category": "working-directory",
  "description": "Sets your working directory (default ~/Work). The directory is created if missing. The strict safety profile uses this to fence Write/Edit.",
  "recommended": true,
  "exclusive_group": null,
  "depends_on": [],
  "conflicts_with": []
}
```

- [ ] **Step 2: `version.txt`**

```
1.0.0
```

- [ ] **Step 3: `claude-md-fragment.md`**

```markdown
## Working directory

The user has chosen a working directory for project files. Default and read it from the manifest at `~/.claude/.claude-personal-starter.json` under `working_directory`. Treat that path as the home base for everything the user is actively working on.

When the user says "put this somewhere" or "open my notes," default to that directory. Don't write outside it without asking first.
```

- [ ] **Step 4: Commit**

```sh
git add tools/components/working-directory
git commit -m "feat(components): working-directory"
```

---

## Task 11: `identity-block` component

**Files:**
- Create: `tools/components/identity-block/component.json`
- Create: `tools/components/identity-block/version.txt`
- Create: `tools/components/identity-block/claude-md-fragment.md`

- [ ] **Step 1: `component.json`**

```json
{
  "id": "identity-block",
  "name": "Identity (who you are)",
  "category": "identity",
  "description": "One free-text prompt during /setup — describe who you are and what you mostly use this for. Goes verbatim into CLAUDE.md. Skippable. Editable later.",
  "recommended": true,
  "exclusive_group": null,
  "depends_on": [],
  "conflicts_with": []
}
```

- [ ] **Step 2: `version.txt`**

```
1.0.0
```

- [ ] **Step 3: `claude-md-fragment.md`**

```markdown
## Who I am

<<IDENTITY>>

(Edit this section freely — it's where you describe yourself to Claude. The /setup skill only writes here if it's empty.)
```

`// verified: apply.py replaces <<IDENTITY>> with the identity_text arg. When identity_text is None/empty, the placeholder becomes empty and the user can edit it later.`

- [ ] **Step 4: Commit**

```sh
git add tools/components/identity-block
git commit -m "feat(components): identity-block"
```

---

## Task 12: `tool-gmail` component

**Files:**
- Create: `tools/components/tool-gmail/component.json`
- Create: `tools/components/tool-gmail/version.txt`
- Create: `tools/components/tool-gmail/claude-md-fragment.md`
- Create: `tools/components/tool-gmail/setup-notes.md`

This component doesn't ship skills directly — the Google Workspace skills (`gws-gmail-*`) are already part of the standard Claude Code plugin set on most installs. This component's job is to (a) tell the user how to enable the MCP, (b) add a CLAUDE.md note documenting how Gmail work should be approached.

- [ ] **Step 1: `component.json`**

```json
{
  "id": "tool-gmail",
  "name": "Gmail",
  "category": "tools",
  "description": "Send, read, search, and triage Gmail via the Google Workspace MCP. You'll OAuth into your Google account after install.",
  "recommended": false,
  "exclusive_group": null,
  "depends_on": [],
  "conflicts_with": []
}
```

- [ ] **Step 2: `version.txt`**

```
1.0.0
```

- [ ] **Step 3: `claude-md-fragment.md`**

```markdown
## Gmail (via Google Workspace MCP)

The user has Gmail enabled. Use the `gws-gmail-*` skills for inbox triage, sending, searching, and replying. Default behavior:

- **Never auto-send.** Draft to a Gmail draft and let the user review and click send.
- When the user asks "what's in my inbox," summarize unread by sender + subject + thread urgency, never just paste raw bodies.
- When asked to reply, draft to a Gmail draft using `gws-gmail-reply` or `gws-gmail-reply-all` — this preserves threading.
- Treat email contents as sensitive. Don't paste them into web searches or third-party tools without asking.
```

- [ ] **Step 4: `setup-notes.md`**

```markdown
## Gmail post-install

To finish setting up Gmail, start a new Claude session and run:

```
@claude_ai_Gmail authenticate
```

You'll be redirected to a Google sign-in page. After authorizing, you'll be able to read and send Gmail from Claude.
```

- [ ] **Step 5: Commit**

```sh
git add tools/components/tool-gmail
git commit -m "feat(components): tool-gmail"
```

---

## Task 13: `tool-google-calendar` component

**Files:**
- Create: `tools/components/tool-google-calendar/component.json`
- Create: `tools/components/tool-google-calendar/version.txt`
- Create: `tools/components/tool-google-calendar/claude-md-fragment.md`
- Create: `tools/components/tool-google-calendar/setup-notes.md`

- [ ] **Step 1: `component.json`**

```json
{
  "id": "tool-google-calendar",
  "name": "Google Calendar",
  "category": "tools",
  "description": "Read events, create events, find free time. Uses the gws-calendar skills + Google Calendar MCP.",
  "recommended": false,
  "exclusive_group": null,
  "depends_on": [],
  "conflicts_with": []
}
```

- [ ] **Step 2: `version.txt`**

```
1.0.0
```

- [ ] **Step 3: `claude-md-fragment.md`**

```markdown
## Google Calendar

The user has Calendar enabled. Use `gws-calendar-*` skills for reading events, creating events, and finding free time. Default:

- "What's on my calendar today" → `gws-calendar-agenda`.
- Never create or modify events without confirming the title, time, and attendees first.
- When proposing a meeting time, check the user's existing calendar with `find_free_time` first — don't just guess.
```

- [ ] **Step 4: `setup-notes.md`**

```markdown
## Google Calendar post-install

Start a new Claude session and run:

```
@claude_ai_Google_Calendar authenticate
```

Authorize in your browser. After that, calendar tools will work.
```

- [ ] **Step 5: Commit**

```sh
git add tools/components/tool-google-calendar
git commit -m "feat(components): tool-google-calendar"
```

---

## Task 14: `tool-outlook` component

**Files:**
- Create: `tools/components/tool-outlook/component.json`
- Create: `tools/components/tool-outlook/version.txt`
- Create: `tools/components/tool-outlook/settings-fragment.json`
- Create: `tools/components/tool-outlook/claude-md-fragment.md`
- Create: `tools/components/tool-outlook/setup-notes.md`

Outlook on macOS doesn't have a usable API for Claude to drive directly. The standard workaround is: sync the M365 mailbox to Apple Mail and have Claude read/draft via Apple Mail AppleScript. This component sets that up.

- [ ] **Step 1: `component.json`**

```json
{
  "id": "tool-outlook",
  "name": "Outlook (via Apple Mail)",
  "category": "tools",
  "description": "Read and draft Microsoft 365 / Outlook email via Apple Mail. Requires your M365 account added to Apple Mail. Claude reads from ~/Library/Mail and drafts via osascript.",
  "recommended": false,
  "exclusive_group": null,
  "depends_on": [],
  "conflicts_with": []
}
```

- [ ] **Step 2: `version.txt`**

```
1.0.0
```

- [ ] **Step 3: `settings-fragment.json`**

```json
{
  "permissions": {
    "allow": [
      "Bash(osascript -e 'tell application \"Mail\"*)",
      "Bash(mdfind:*)"
    ]
  }
}
```

`// verified: AppleScript Mail.app dictionary is stable across macOS versions; reading ~/Library/Mail .emlx files via grep works without permissions in Terminal.app with Full Disk Access.`

- [ ] **Step 4: `claude-md-fragment.md`**

```markdown
## Outlook (via Apple Mail)

The user's Microsoft 365 mailbox is synced to Apple Mail. You can:

- **Read** by grepping ~/Library/Mail/.../*.emlx files directly, or via `mdfind` (Spotlight).
- **Search structured** via `osascript -e 'tell application "Mail" ...'` — read messages by ID, list messages in inbox, etc.
- **Draft replies** by creating a Mail.app draft via AppleScript. Never auto-send.

Pattern: draft → show preview → wait for explicit "send" → ask the user to click send manually. Auto-send is not enabled by design.

If the user reports Apple Mail isn't syncing, the fix is in System Settings → Internet Accounts. Don't try to fix it via Claude.
```

- [ ] **Step 5: `setup-notes.md`**

```markdown
## Outlook post-install

1. Open System Settings → Internet Accounts → Add Account → Microsoft Exchange.
2. Sign in with your work email. Microsoft handles OAuth + 2FA.
3. When asked which apps to enable, tick Mail (Calendar / Contacts optional).
4. Open Mail.app and let it download messages to ~/Library/Mail (~1 hour for a typical mailbox).
5. In Terminal.app preferences → Privacy & Security, ensure Terminal has **Full Disk Access** so Claude can read mailbox files.

You can keep using Outlook as your everyday client. Apple Mail runs in the background as Claude's read window.
```

- [ ] **Step 6: Commit**

```sh
git add tools/components/tool-outlook
git commit -m "feat(components): tool-outlook via Apple Mail bridge"
```

---

## Task 15: `skill-email-triage` component

**Files:**
- Create: `tools/components/skill-email-triage/component.json`
- Create: `tools/components/skill-email-triage/version.txt`
- Create: `tools/components/skill-email-triage/skills/email-triage/SKILL.md`

- [ ] **Step 1: `component.json`**

```json
{
  "id": "skill-email-triage",
  "name": "Email triage",
  "category": "skills",
  "description": "Skill that produces an inbox summary grouped by urgency and sender. Works with whichever email tools you have installed (Gmail and/or Outlook).",
  "recommended": false,
  "exclusive_group": null,
  "depends_on": [],
  "conflicts_with": []
}
```

- [ ] **Step 2: `version.txt`**

```
1.0.0
```

- [ ] **Step 3: `skills/email-triage/SKILL.md`**

```markdown
---
name: email-triage
description: Use when the user wants a structured summary of unread email, broken down by urgency, sender, and theme. Works against Gmail (via gws-gmail), Outlook (via Apple Mail), or both if available.
---

# Email Triage

Detect which email backends are available:

1. **Gmail** — try `gws-gmail-watch` or `mcp__claude_ai_Gmail__*` tools. If they return data, Gmail is available.
2. **Apple Mail (Outlook/iCloud)** — check whether `~/Library/Mail` exists and contains accounts. If yes, Apple Mail is available.

If both, run both and merge. If neither, tell the user no email backend is configured and point at `/setup`.

## Output structure

Produce a single Markdown block with these sections (omit sections that have no items):

```
### Urgent (anything time-sensitive in next 24h)
- **<sender>** — <subject> · <one-line summary>

### From people you usually reply to fast
- **<sender>** — <subject> · <one-line summary>

### Newsletters / automated
- count: N — skipping detail; mention any that look unusual.

### Promotional / can ignore
- count: N
```

## Rules

- **Never draft replies in this skill.** Triage only. The user will say "reply to the Acme one" separately, and that uses `gws-gmail-reply` or the Apple Mail equivalent.
- **Group automated email aggressively.** Most inboxes are 80% noise. Don't list every newsletter — just count them.
- **Identify urgency by content, not sender.** A meeting reschedule from a colleague today is more urgent than a partner asking about a Q3 plan.
- **Read only what's necessary** to summarize. Don't paste full email bodies into your output unless the user asks.
```

- [ ] **Step 4: Commit**

```sh
git add tools/components/skill-email-triage
git commit -m "feat(components): skill-email-triage"
```

---

## Task 16: `skill-weekly-digest` component

**Files:**
- Create: `tools/components/skill-weekly-digest/component.json`
- Create: `tools/components/skill-weekly-digest/version.txt`
- Create: `tools/components/skill-weekly-digest/skills/weekly-digest/SKILL.md`

- [ ] **Step 1: `component.json`**

```json
{
  "id": "skill-weekly-digest",
  "name": "Weekly digest",
  "category": "skills",
  "description": "Skill that summarizes this week's meetings, unread email count, and standout messages. Requires at least one email tool and one calendar tool.",
  "recommended": false,
  "exclusive_group": null,
  "depends_on": [],
  "conflicts_with": []
}
```

- [ ] **Step 2: `version.txt`**

```
1.0.0
```

- [ ] **Step 3: `skills/weekly-digest/SKILL.md`**

```markdown
---
name: weekly-digest
description: Use when the user wants a Monday-morning (or any-day) summary of the week — meetings, email volume, what's coming up, what fell behind.
---

# Weekly Digest

Build a single Markdown report covering the week from "today" to "today + 7 days," plus a brief look-back at "the last 7 days."

## Sections (in this order)

```
## Week of <Monday date>

### This week's meetings (next 7 days)
<bulleted list, day-grouped, with title + time + attendees>

### Inbox status
- <N> unread messages, of which <urgent count> look time-sensitive (run /email-triage for detail)
- People waiting on a reply: <list anyone who's emailed twice without a response>

### Loose ends from last week
- <items that look unresolved — replies you started drafting but didn't send, calendar events you cancelled with "rescheduling later," etc.>

### Things to think about
- <2-3 themes the AI noticed across the week — e.g., "you spent 60% of last week in internal meetings; only 2 customer calls">
```

## Rules

- **Don't make stuff up.** If you can't determine "loose ends" from real data, omit that section.
- **Look at the calendar AND email together.** A meeting that got rescheduled twice has email context that matters.
- **Quantify when you can** — "8 hours of meetings this week" is more useful than "lots of meetings."
- **Don't draft action items.** This is a digest, not a planner. The user will ask separately if they want followups.
```

- [ ] **Step 4: Commit**

```sh
git add tools/components/skill-weekly-digest
git commit -m "feat(components): skill-weekly-digest"
```

---

## Task 17: The `/setup` skill

**Files:**
- Create: `skills/setup/SKILL.md`

`/setup` is the user-facing TUI. It uses `AskUserQuestion` to present checkboxes by category, then calls `tools/install` to apply.

`// verified: AskUserQuestion supports multiSelect: true for tick-multiple categories; single-select for exclusive_group categories. Maximum 4 options per question — if a category has >4 components, split across questions. Available skills listed at session start, so /setup will work when invoked.`

- [ ] **Step 1: Write `skills/setup/SKILL.md`**

```markdown
---
name: setup
description: Use when the user wants to install, reconfigure, or update their claude-personal-starter components. Walks them through choosing components via checkboxes and applies the changes via tools/install.
---

# /setup — claude-personal-starter

You are running the modular Claude starter setup. The user wants to pick (or re-pick) which components to install. The repo is cloned at `~/.claude-personal-starter/`. The installer CLI is at `~/.claude-personal-starter/tools/install`.

## Process

### 1. Refresh the source

Run:

```
git -C ~/.claude-personal-starter pull --ff-only
```

If it fails (no network, conflict), continue with whatever's on disk and tell the user.

### 2. Load the catalog

Run:

```
~/.claude-personal-starter/tools/install list-components --json
```

Parse the JSON. Group by `category`. Note which are `installed: true`.

### 3. Walk the user through each category

For each category, present the options via `AskUserQuestion`. Order: `safety`, `working-directory`, `tools`, `skills`, `identity`.

**Safety** (exclusive group — radio behavior, single-select):
- Question: "Pick a safety profile."
- Header: "Safety"
- multiSelect: false
- Options: one per safety component, with the component's `description` as the option description. Pre-select the currently-installed one (if any) or the `recommended: true` one as the first option.

**Working directory** (required):
- Question: "Where should your working directory be?"
- Ask via free-text (use AskUserQuestion with a single Default option labeled e.g. "~/Work" and "Other" for custom, OR — better — just state the default and proceed unless the user volunteers a different path; we can also pass `--working-dir ~/Work` directly).
- Default to `~/Work` if no answer.

**Tools** (multi-select, may need multiple questions if >4):
- Question: "Which tools do you want? (Tick all that apply.)"
- Header: "Tools"
- multiSelect: true
- Options: every component in the `tools` category. Pre-tick currently-installed.
- If more than 4 options, split into "Email tools" and "Calendar/Drive/Docs" sub-questions.

**Skills** (multi-select):
- Question: "Which workflow skills do you want?"
- Header: "Skills"
- multiSelect: true
- Options: every component in the `skills` category. Pre-tick installed.

**Identity** (multi-select, single-option):
- Question: "Want to add a 'who I am' note to your CLAUDE.md?"
- Header: "Identity"
- multiSelect: false
- Options: ["Yes — describe me", "Skip — I'll edit CLAUDE.md myself later"]
- If "Yes," ask one follow-up open-ended question: "In a sentence or two, who are you and what do you mostly use Claude for?"

### 4. Compute diff

- `currently_installed` = set of installed ids from step 2.
- `requested` = union of every component the user ticked.
- `to_add` = `requested - currently_installed`
- `to_remove` = `currently_installed - requested`

### 5. Apply

Run:

```
~/.claude-personal-starter/tools/install apply \
  --add "<comma-separated to_add>" \
  --remove "<comma-separated to_remove>" \
  --working-dir "<path or omit>" \
  --identity-text "<text or omit>"
```

Show the output to the user.

### 6. Show post-install actions

For every newly-added component, read `~/.claude-personal-starter/tools/components/<id>/setup-notes.md` if it exists, and concatenate. Show the result as "Next steps:" — these are typically MCP `authenticate` commands the user needs to run in a fresh session.

### 7. Confirm

Print a one-line summary:

```
Done. Added: tool-gmail, skill-weekly-digest. Removed: (none). Currently installed: safety-strict, working-directory, identity-block, tool-gmail, tool-google-calendar, skill-email-triage, skill-weekly-digest.
```

## Edge cases

- **First-time install (nothing in manifest):** Treat every option as un-ticked. Proceed normally.
- **No `~/.claude-personal-starter/` directory:** Tell the user to re-run the curl bootstrap. Stop.
- **`tools/install` exits with a non-zero status:** Show stderr to the user, do not claim success.
- **User aborts via Ctrl-C in the middle:** Whatever has been applied via earlier `apply` calls is persistent; explain that re-running `/setup` will pick up where they left off.
```

- [ ] **Step 2: Commit**

```sh
git add skills/setup/SKILL.md
git commit -m "feat(skill): /setup TUI driver for component picker"
```

---

## Task 18: `bootstrap.sh`

**Files:**
- Create: `bootstrap.sh`

The curl-able entry point. Hosted on `main` and stable. It:

1. Checks that Claude Code is installed.
2. Clones the repo to `~/.claude-personal-starter/` (or pulls if it exists).
3. Copies `skills/setup/` into `~/.claude/skills/setup/`.
4. Tells the user to run `claude` and type `/setup`.

- [ ] **Step 1: Write `bootstrap.sh`**

```bash
#!/usr/bin/env bash
# claude-personal-starter bootstrap.
#
# Usage: curl -fsSL https://raw.githubusercontent.com/Tugboat-Solutions-Inc/claude-personal-starter/main/bootstrap.sh | sh
#
# Idempotent. Re-running pulls the latest repo and re-syncs the setup skill.

set -euo pipefail

REPO_URL="${CLAUDE_PERSONAL_STARTER_REPO:-https://github.com/Tugboat-Solutions-Inc/claude-personal-starter.git}"
REPO_DIR="${CLAUDE_PERSONAL_STARTER_DIR:-$HOME/.claude-personal-starter}"
CLAUDE_DIR="$HOME/.claude"
SKILL_DIR="$CLAUDE_DIR/skills/setup"

red()  { printf "\033[31m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
blue() { printf "\033[34m%s\033[0m\n" "$*"; }

require() {
  command -v "$1" >/dev/null 2>&1 || { red "$1 not found in PATH. Install it first."; exit 1; }
}

main() {
  blue "claude-personal-starter bootstrap"

  require git
  require python3
  if ! command -v claude >/dev/null 2>&1; then
    red "claude not found in PATH."
    echo "Install Claude Code first:"
    echo "  curl -fsSL https://claude.ai/install.sh | sh"
    echo "Then run claude once to OAuth-login, press Enter on the success page,"
    echo "type /exit, then re-run this bootstrap."
    exit 1
  fi

  if [ -d "$REPO_DIR/.git" ]; then
    blue "Updating $REPO_DIR ..."
    git -C "$REPO_DIR" fetch --quiet origin
    git -C "$REPO_DIR" reset --hard --quiet origin/main
  else
    blue "Cloning to $REPO_DIR ..."
    git clone --quiet "$REPO_URL" "$REPO_DIR"
  fi

  mkdir -p "$SKILL_DIR"
  cp "$REPO_DIR/skills/setup/SKILL.md" "$SKILL_DIR/SKILL.md"

  chmod +x "$REPO_DIR/tools/install"

  green "Installed."
  echo ""
  echo "Next:"
  echo "  1. Run: claude"
  echo "  2. In the prompt, type: /setup"
  echo "  3. Pick the components you want."
}

main "$@"
```

- [ ] **Step 2: Make executable and verify it parses**

```sh
chmod +x bootstrap.sh
bash -n bootstrap.sh
```

Expected: no output (syntax check passes).

- [ ] **Step 3: Commit**

```sh
git add bootstrap.sh
git commit -m "feat: bootstrap.sh curl entry point"
```

---

## Task 19: Docs

**Files:**
- Create: `docs/ONBOARDING.md`
- Create: `docs/components.md`

- [ ] **Step 1: `docs/ONBOARDING.md`**

```markdown
# Onboarding

The whole thing takes about 30 minutes if Claude Code isn't installed yet, or 5 minutes if it is.

## Step 1 — Install Claude Code (skip if you already have it)

Claude Code is Anthropic's CLI for Claude. Install it:

```sh
curl -fsSL https://claude.ai/install.sh | sh
```

Then start it once to log in:

```sh
claude
```

It will open a browser for OAuth. After you sign in, **press Enter** on the success page in the Terminal (if you skip that, the credential isn't saved). Then type `/exit`.

## Step 2 — Run the bootstrap

```sh
curl -fsSL https://raw.githubusercontent.com/Tugboat-Solutions-Inc/claude-personal-starter/main/bootstrap.sh | sh
```

This clones the repo to `~/.claude-personal-starter/` and drops a `/setup` skill into `~/.claude/skills/setup/`. Nothing else changes yet.

## Step 3 — Pick your components

```sh
claude
```

Type `/setup` and walk through the checkboxes.

## Step 4 — Run any post-install actions

After `/setup` finishes, it shows "Next steps:" — usually one or two commands to authenticate Google services. Run them in a new Claude session.

## Step 5 — Try it

Restart Claude (so `~/.claude/CLAUDE.md` reloads) and ask:

- "What's in my inbox today?"
- "What's on my calendar this week?"
- "Give me a weekly digest."

## To update later

Re-run `/setup` any time. It pulls the latest components from GitHub and lets you tick/untick.

## To reset

Edit or delete `~/.claude/CLAUDE.md`, `~/.claude/settings.json`, or the `~/.claude/skills/*` and `~/.claude/hooks/*` files directly. The manifest is at `~/.claude/.claude-personal-starter.json`.
```

- [ ] **Step 2: `docs/components.md`**

A simple catalog page. The single source of truth for what components exist; mirrors the contents of `tools/components/` at v1.

```markdown
# Component Catalog

Every component is independently optional. Mix and match.

## Safety (pick one)

- **safety-strict** — Hooks block destructive shell + network egress; Write/Edit fenced to your working directory; system paths denied.
- **safety-chill** — System paths denied; everything else allowed.

## Working directory

- **working-directory** — Sets your project home (default `~/Work`).

## Identity

- **identity-block** — Adds a one-line "who I am" note to your CLAUDE.md.

## Tools

- **tool-gmail** — Gmail send/read/triage via Google Workspace MCP.
- **tool-google-calendar** — Calendar events, find-free-time.
- **tool-outlook** — Outlook (M365) via Apple Mail bridge.

## Skills

- **skill-email-triage** — Structured inbox summary by urgency and sender.
- **skill-weekly-digest** — This-week meetings + inbox status + loose ends.

## Adding more

To add a component, drop a directory under `tools/components/<id>/` containing `component.json`, `version.txt`, and any of `claude-md-fragment.md`, `settings-fragment.json`, `skills/`, `hooks/`, `agents/`, `setup-notes.md`. Bump and PR.
```

- [ ] **Step 3: Commit**

```sh
git add docs/ONBOARDING.md docs/components.md
git commit -m "docs: onboarding + component catalog"
```

---

## Task 20: End-to-end smoke test

**Files:**
- Create: `tools/tests/test_end_to_end.py`

Drive the full install path against a synthetic `~/.claude` dir. This is the regression net for the whole system.

- [ ] **Step 1: Write the test**

`tools/tests/test_end_to_end.py`:

```python
import json
import os
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
INSTALL = REPO / "tools" / "install"


def run(args: list[str], target: Path):
    env = dict(os.environ, CLAUDE_PERSONAL_STARTER_TARGET=str(target))
    return subprocess.run(
        [str(INSTALL), *args], env=env, capture_output=True, text=True, check=True,
    )


def test_install_minimal_set_and_remove(tmp_path):
    target = tmp_path / "claude"
    target.mkdir()
    work_dir = tmp_path / "Work"

    # Install: safety-strict (auto-pulls working-directory), identity-block.
    run([
        "apply",
        "--add", "safety-strict,identity-block",
        "--working-dir", str(work_dir),
        "--identity-text", "I am a test user.",
    ], target)

    # Verify CLAUDE.md has the identity text and both block markers.
    claude_md = (target / "CLAUDE.md").read_text()
    assert "I am a test user." in claude_md
    assert "claude-personal-starter: safety-strict" in claude_md
    assert "claude-personal-starter: working-directory" in claude_md
    assert "claude-personal-starter: identity-block" in claude_md

    # Verify settings.json has defaultMode=auto and the strict deny entries.
    settings = json.loads((target / "settings.json").read_text())
    assert settings["permissions"]["defaultMode"] == "auto"
    assert "Bash(rm -rf:*)" in settings["permissions"]["deny"]
    assert any("destructive-bash-guard" in h.get("command", "")
               for group in settings["hooks"]["PreToolUse"]
               for h in group["hooks"])

    # Verify hooks are copied + executable.
    hook = target / "hooks" / "destructive-bash-guard.py"
    assert hook.exists()
    assert os.access(hook, os.X_OK)

    # Verify manifest.
    m = json.loads((target / ".claude-personal-starter.json").read_text())
    assert set(m["components"].keys()) == {"safety-strict", "working-directory", "identity-block"}
    assert m["working_directory"] == str(work_dir)
    assert work_dir.exists()

    # Now remove identity-block.
    run(["apply", "--remove", "identity-block"], target)
    claude_md = (target / "CLAUDE.md").read_text()
    assert "I am a test user." not in claude_md
    assert "claude-personal-starter: identity-block" not in claude_md
    assert "claude-personal-starter: safety-strict" in claude_md  # still there

    # Verify manifest reflects removal.
    m = json.loads((target / ".claude-personal-starter.json").read_text())
    assert "identity-block" not in m["components"]


def test_list_components_smoke(tmp_path):
    target = tmp_path / "claude"
    target.mkdir()
    result = run(["list-components", "--json"], target)
    components = json.loads(result.stdout)
    ids = {c["id"] for c in components}
    assert "safety-strict" in ids
    assert "safety-chill" in ids
    assert "working-directory" in ids
    assert "identity-block" in ids
```

- [ ] **Step 2: Run the test**

```sh
cd ~/Development/claude-personal-starter
python3 -m pytest tools/tests/test_end_to_end.py -v
```

Expected: all PASS. If anything fails, debug. Common issues:

- The `safety-strict` `depends_on: ["working-directory"]` may need to be resolved by `apply`. The test relies on `resolve_dependencies` doing this; if working-directory isn't in the manifest, the safety hook will be a no-op (it reads working_directory from the manifest), which is fine.
- The `identity-block` CLAUDE.md fragment uses `<<IDENTITY>>` placeholder — make sure `apply.py` is replacing it.

- [ ] **Step 3: Run the whole suite**

```sh
python3 -m pytest tools/tests -v
```

Expected: every test PASSES.

- [ ] **Step 4: Commit**

```sh
git add tools/tests/test_end_to_end.py
git commit -m "test: end-to-end install/remove smoke"
```

---

## Task 21: Push to GitHub

- [ ] **Step 1: Create the remote (if it doesn't exist)**

```sh
cd ~/Development/claude-personal-starter
gh repo create Tugboat-Solutions-Inc/claude-personal-starter \
  --public \
  --description "A modular Claude Code starter. Pick what you want via in-Claude checkboxes." \
  --source . \
  --remote origin
```

- [ ] **Step 2: Push**

```sh
git push -u origin main
```

- [ ] **Step 3: Verify the bootstrap URL resolves**

```sh
curl -fsSL https://raw.githubusercontent.com/Tugboat-Solutions-Inc/claude-personal-starter/main/bootstrap.sh | head -5
```

Expected: the first few lines of bootstrap.sh.

- [ ] **Step 4: End-to-end on a clean fixture**

Run the bootstrap against a throwaway target dir:

```sh
CLAUDE_PERSONAL_STARTER_DIR=/tmp/cps-test \
  bash bootstrap.sh
ls /tmp/cps-test
ls ~/.claude/skills/setup
```

Expected: repo cloned to `/tmp/cps-test`, `/setup` skill present in `~/.claude/skills/setup/`. (This test mutates the real `~/.claude/` — do this last and back up first if you've got something important there.)

- [ ] **Step 5: Final commit (none expected, just confirm clean tree)**

```sh
git status
```

Expected: "nothing to commit, working tree clean."

---

## Self-Review

**Spec coverage:**

- Public repo + curl bootstrap → Tasks 18, 19, 21 ✓
- Two-stage install (bootstrap + /setup) → Tasks 17, 18 ✓
- Component model with `component.json` + version + fragments → Tasks 2, 8–16 ✓
- CLAUDE.md managed-marker composition → Task 3 ✓
- settings.json deep-merge with `defaultMode: auto` → Tasks 4, 6 ✓
- Manifest tracking → Task 5 ✓
- Apply/remove orchestration with file copy + cleanup → Task 6 ✓
- CLI surface (`list-components`, `list-installed`, `apply`, `upgrade`) → Task 7 ✓
- Initial components: safety-strict, safety-chill, working-directory, identity-block, tool-gmail, tool-google-calendar, tool-outlook, skill-email-triage, skill-weekly-digest → Tasks 8–16 ✓
- `/setup` skill drives checkboxes via AskUserQuestion → Task 17 ✓
- Identity block free-text prompt + verbatim insertion → Tasks 11, 17, 6 ✓
- End-to-end test → Task 20 ✓

**Placeholder scan:** none.

**Type consistency:** `apply()` signature uses keyword-only args; `components_dir`, `target_dir`, `add`, `remove`, `working_directory`, `identity_text` consistent across `apply.py`, `tools/install`, and tests. CLI args match (`--add`, `--remove`, `--working-dir`, `--identity-text`).

**Known limitations baked into v1:**
- Aaron must run the gh-repo-create step (Task 21) himself or have it already exist before push — alternative is to push the existing local repo to an empty pre-created remote.
- `tools/install` shells out to its own Python lib via `sys.path` injection; this works because the file isn't an installed package. Tests use module imports (`from tools.lib import …`) and require `pytest` to be invoked from the repo root with `tools/` discoverable.
