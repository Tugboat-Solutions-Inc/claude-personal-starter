---
name: setup
description: Use when the user wants to install, reconfigure, or update their claude-personal-starter components. Walks them through choosing components via checkboxes and applies the changes by editing their CLAUDE.md, settings.json, and copying skills/hooks directly.
---

# /setup — claude-personal-starter

You are walking the user through installing or reconfiguring components from `claude-personal-starter`. The repo is cloned at `~/.claude-personal-starter/`. There is no Python CLI — **you do the work directly** using your normal Read, Edit, Write, and Bash tools.

This skill is rerunnable. The user can `/setup` any time to add or remove components.

---

## Step 1 — Refresh the source

Run:

```
git -C ~/.claude-personal-starter pull --ff-only
```

If it fails (no network, conflict, dirty tree), continue with whatever's on disk and tell the user briefly.

If `~/.claude-personal-starter/` doesn't exist at all, stop and tell the user to run the bootstrap:

```
curl -fsSL https://raw.githubusercontent.com/Tugboat-Solutions-Inc/claude-personal-starter/main/bootstrap.sh | sh
```

---

## Step 2 — Discover components

List directories under `~/.claude-personal-starter/components/`. For each one, Read its `component.json` to get `id`, `name`, `category`, `description`, `recommended`, `exclusive_group`, and `depends_on` (optional, defaults to empty).

Group components by `category`. Standard categories in display order:

1. `safety` (exclusive — pick one)
2. `working-directory`
3. `tools` (multi-select)
4. `skills` (multi-select)
5. `identity`

If you find a category you don't recognize, render it after the standard ones with `multiSelect: true` and proceed.

Detect what's already installed by reading the user's `~/.claude/CLAUDE.md` (if present) and grepping for each component's `claude-md.md` section heading. The first `## ` line of each component's `claude-md.md` is the marker — if it appears in the user's CLAUDE.md, that component is currently applied.

---

## Step 3 — Walk the user through the picker

For each category, call `AskUserQuestion`:

- **Safety**: `multiSelect: false`. Options are the safety components in that category. Pre-select the currently-installed one if any; otherwise the `recommended: true` one. Description on each option = the component's `description`.
- **Working directory**: ask one open-ended question via the text-input fallback (use a single option labeled with the default `~/Work` plus an "Other" path the user can type). Default: `~/Work`. Resolve `~` to an absolute path before using it (`os.path.expanduser` equivalent — just shell-expand or call `bash -c 'echo ~/Work'` via Bash).
- **Tools**: `multiSelect: true`. Options are every component in the `tools` category. Pre-tick currently-installed. If there are more than 4, split into two questions ("Email tools", "Calendar/Drive/Docs/etc.") — `AskUserQuestion` caps at 4 options per question.
- **Skills**: `multiSelect: true`. Same pattern.
- **Identity**: `multiSelect: false`. Options: ["Yes — describe me", "Skip — I'll edit CLAUDE.md myself later"]. If "Yes," follow up with one open-ended question: "In a sentence or two, who are you and what do you mostly use Claude for?"

Compute:

- `to_add` = picked components that aren't currently installed
- `to_remove` = currently-installed components that the user unticked

---

## Step 4 — Apply changes

For each component in `to_remove` (process removes before adds):

1. **CLAUDE.md**: Read `~/.claude/CLAUDE.md`. Read the component's `claude-md.md` to find its section heading. Remove that section from the user's CLAUDE.md (from the heading through the line before the next `## ` heading, or end of file).
2. **settings.json**: Read the component's `settings.json` (if present). Read the user's `~/.claude/settings.json`. Remove the component's contributions: strip its entries from `permissions.allow` and `permissions.deny`; strip its hook commands from any matcher group (and drop matcher groups whose `hooks` list becomes empty); remove its `env` keys.
3. **Hooks**: For each file in the component's `hooks/`, delete the corresponding `~/.claude/hooks/<basename>`.
4. **Skills**: For each directory in the component's `skills/`, delete the corresponding `~/.claude/skills/<dirname>`.

For each component in `to_add`:

1. **Resolve dependencies**: if the component has `depends_on`, ensure those components are also being installed (auto-add them).
2. **CLAUDE.md**: Read the component's `claude-md.md`. Substitute `<<IDENTITY>>` with the user's identity text (if applicable) and `<<WORKING_DIR>>` with the absolute working directory path. Read the user's `~/.claude/CLAUDE.md` (initialize empty if absent). If the component's section heading is already present, replace that section; otherwise append to the end with one blank line before. Write back.
3. **settings.json**: Read the component's `settings.json` (if present). Read the user's `~/.claude/settings.json` (initialize from this base if absent: `{"$schema": "https://json.schemastore.org/claude-code-settings.json", "permissions": {"defaultMode": "auto", "allow": [], "deny": []}, "hooks": {}, "env": {}}`). Merge: union `allow` and `deny` (deduped); for `hooks`, find matching matcher groups and union their `hooks` arrays by command, otherwise add the matcher group; shallow-merge `env`. Write back.
4. **Hooks**: For each file in the component's `hooks/`, Read it, substitute `<<WORKING_DIR>>` with the absolute working directory path if present, write to `~/.claude/hooks/<basename>`, `chmod +x`.
5. **Skills**: Recursively copy each directory in the component's `skills/` into `~/.claude/skills/`.

---

## Step 5 — Show next steps

For every component in `to_add`, Read its `INSTALL.md` if it exists. Concatenate them. Present to the user under the heading "**Next steps:**". These are usually OAuth or MCP authenticate commands the user runs from a fresh Claude session.

Then print a one-line summary of what changed:

```
Done. Added: <list>. Removed: <list>. Currently installed: <list>.
```

If the user added or removed `safety-strict` or `working-directory`, mention that they should restart Claude Code so the hooks reload.

---

## Edge cases

- **Empty `~/.claude/CLAUDE.md`**: treat as starting from scratch.
- **User's CLAUDE.md has unrelated content above your sections**: leave it alone. Append at the end.
- **JSON parse error in user's settings.json**: stop. Tell the user the file is malformed and ask them to fix it (or back it up and let you regenerate from scratch).
- **Component file missing on disk** (e.g., `claude-md.md` not present): just skip that step for that component — not all components have all files.
- **`AskUserQuestion` 4-option cap**: split into multiple questions for any category with >4 components.
- **`<<WORKING_DIR>>` not yet decided when applying a hook**: ask the user for the working directory first, before any hook copying.
