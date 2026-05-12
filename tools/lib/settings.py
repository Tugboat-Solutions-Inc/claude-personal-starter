"""Deep-merge settings.json fragments from components."""
from copy import deepcopy


def merge_fragments(base: dict, fragments: list) -> dict:
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


def _merge_matcher_group(existing: list, incoming: dict) -> None:
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


def _strip_matcher_group(existing: list, incoming: dict) -> None:
    matcher = incoming.get("matcher")
    target = next((g for g in existing if g.get("matcher") == matcher), None)
    if target is None:
        return
    bad = {(h.get("type"), h.get("command")) for h in incoming.get("hooks", [])}
    target["hooks"] = [h for h in target.get("hooks", []) if (h.get("type"), h.get("command")) not in bad]
