import json

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
        "id": "tool-z",
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
