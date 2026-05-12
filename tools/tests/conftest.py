import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_components_dir(tmp_path):
    """A temp dir mimicking tools/components/, returned as Path."""
    d = tmp_path / "components"
    d.mkdir()
    return d


def write_component(parent: Path, id: str, meta: dict, fragments: dict | None = None):
    """Create a component dir with component.json and optional fragment files."""
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
