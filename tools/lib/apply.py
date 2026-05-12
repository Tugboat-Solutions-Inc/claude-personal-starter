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
    components_dir,
    target_dir,
    add: set,
    remove: set,
    working_directory,
    identity_text,
) -> None:
    components_dir = Path(components_dir)
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    components = catalog.load_components(components_dir)
    catalog.validate_catalog(components)

    manifest_path = target_dir / ".claude-personal-starter.json"
    state = manifest.read(manifest_path)
    installed = set(state["components"].keys())

    add_closure = catalog.resolve_dependencies(components, list(add)) - installed if add else set()
    final_installed = (installed - remove) | add_closure
    catalog.check_conflicts(components, final_installed)

    for cid in sorted(remove):
        if cid in installed:
            _remove_one(target_dir, cid, components.get(cid), state["components"][cid])
            manifest.record_remove(manifest_path, cid)

    for cid in sorted(add_closure):
        _install_one(target_dir, components[cid], manifest_path, identity_text)

    if working_directory is not None:
        Path(working_directory).expanduser().mkdir(parents=True, exist_ok=True)
        manifest.set_working_directory(manifest_path, working_directory)


def _install_one(target_dir: Path, component: dict, manifest_path: Path,
                  identity_text) -> None:
    cid = component["id"]
    src = component["source_path"]

    files_copied = []
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

    settings_fragment_file = src / "settings-fragment.json"
    contribution = {"allow": [], "deny": [], "env": {}, "hooks": {}}
    if settings_fragment_file.exists():
        fragment = json.loads(settings_fragment_file.read_text())
        contribution = settings_mod.compute_contribution(cid, fragment)
        settings_path = target_dir / "settings.json"
        existing = json.loads(settings_path.read_text()) if settings_path.exists() else dict(BASE_SETTINGS)
        merged = settings_mod.merge_fragments(existing, [(cid, fragment)])
        settings_path.write_text(json.dumps(merged, indent=2) + "\n")

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


def _remove_one(target_dir: Path, cid: str, component, manifest_entry: dict) -> None:
    for rel in manifest_entry.get("files_copied", []):
        f = target_dir / rel
        if f.exists():
            f.unlink()
            parent = f.parent
            while parent != target_dir and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent

    claude_md_path = target_dir / "CLAUDE.md"
    if claude_md_path.exists():
        existing = claude_md_path.read_text()
        blocks, freeform = claude_md.parse_blocks(existing)
        blocks, freeform = claude_md.apply_changes(blocks, freeform, add={}, remove={cid})
        claude_md_path.write_text(claude_md.compose(blocks, freeform))

    settings_path = target_dir / "settings.json"
    if settings_path.exists():
        existing = json.loads(settings_path.read_text())
        stripped = settings_mod.remove_contribution(existing, manifest_entry.get("settings_contribution", {}))
        settings_path.write_text(json.dumps(stripped, indent=2) + "\n")
