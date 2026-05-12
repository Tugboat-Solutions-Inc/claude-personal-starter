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
