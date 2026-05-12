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
    for child in sorted(Path(components_dir).iterdir()):
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


def resolve_dependencies(components: dict, requested) -> set:
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


def check_conflicts(components: dict, selected: set) -> None:
    """Raise CatalogError if the selected set contains direct conflicts or
    multiple members of the same exclusive_group."""
    for cid in selected:
        c = components[cid]
        for conf in c["conflicts_with"]:
            if conf in selected:
                raise CatalogError(f"{cid} conflicts with {conf}")
    groups: dict = {}
    for cid in selected:
        group = components[cid].get("exclusive_group")
        if group:
            groups.setdefault(group, []).append(cid)
    for group, members in groups.items():
        if len(members) > 1:
            raise CatalogError(f"exclusive_group={group}: multiple selected {sorted(members)}")
