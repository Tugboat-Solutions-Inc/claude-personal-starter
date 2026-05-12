import json
import os
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
INSTALL = REPO / "tools" / "install"


def run(args, target):
    env = dict(os.environ, CLAUDE_PERSONAL_STARTER_TARGET=str(target))
    return subprocess.run(
        [str(INSTALL), *args], env=env, capture_output=True, text=True, check=True,
    )


def test_install_minimal_set_and_remove(tmp_path):
    target = tmp_path / "claude"
    target.mkdir()
    work_dir = tmp_path / "Work"

    run([
        "apply",
        "--add", "safety-strict,identity-block",
        "--working-dir", str(work_dir),
        "--identity-text", "I am a test user.",
    ], target)

    claude_md = (target / "CLAUDE.md").read_text()
    assert "I am a test user." in claude_md
    assert "claude-personal-starter: safety-strict" in claude_md
    assert "claude-personal-starter: working-directory" in claude_md
    assert "claude-personal-starter: identity-block" in claude_md

    settings = json.loads((target / "settings.json").read_text())
    assert settings["permissions"]["defaultMode"] == "auto"
    assert "Bash(rm -rf:*)" in settings["permissions"]["deny"]
    assert any("destructive-bash-guard" in h.get("command", "")
               for group in settings["hooks"]["PreToolUse"]
               for h in group["hooks"])

    hook = target / "hooks" / "destructive-bash-guard.py"
    assert hook.exists()
    assert os.access(hook, os.X_OK)

    m = json.loads((target / ".claude-personal-starter.json").read_text())
    assert set(m["components"].keys()) == {"safety-strict", "working-directory", "identity-block"}
    assert m["working_directory"] == str(work_dir)
    assert work_dir.exists()

    run(["apply", "--remove", "identity-block"], target)
    claude_md = (target / "CLAUDE.md").read_text()
    assert "I am a test user." not in claude_md
    assert "claude-personal-starter: identity-block" not in claude_md
    assert "claude-personal-starter: safety-strict" in claude_md

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
