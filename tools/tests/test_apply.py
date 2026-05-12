import json
from pathlib import Path

from tools.lib import apply, manifest


def _write_component(components_dir: Path, cid: str, *, settings_fragment=None,
                      claude_md_fragment=None, skill_files=None,
                      depends_on=None):
    d = components_dir / cid
    d.mkdir()
    (d / "component.json").write_text(json.dumps({
        "id": cid, "name": cid, "category": "tools", "description": cid,
        "recommended": False, "exclusive_group": None,
        "depends_on": depends_on or [], "conflicts_with": [],
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
