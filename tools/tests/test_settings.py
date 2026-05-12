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
