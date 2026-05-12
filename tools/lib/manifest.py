"""Read/write the install manifest at ~/.claude/.claude-personal-starter.json."""
import json
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1


def _empty() -> dict:
    return {"version": SCHEMA_VERSION, "components": {}, "working_directory": None}


def read(path) -> dict:
    path = Path(path)
    if not path.exists():
        return _empty()
    data = json.loads(path.read_text())
    data.setdefault("version", SCHEMA_VERSION)
    data.setdefault("components", {})
    data.setdefault("working_directory", None)
    return data


def write(path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def record_install(
    path,
    component_id: str,
    version: str,
    files_copied: list,
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


def record_remove(path, component_id: str) -> None:
    data = read(path)
    data["components"].pop(component_id, None)
    write(path, data)


def set_working_directory(path, working_directory: str) -> None:
    data = read(path)
    data["working_directory"] = working_directory
    write(path, data)


def installed_ids(path) -> set:
    return set(read(path)["components"].keys())
