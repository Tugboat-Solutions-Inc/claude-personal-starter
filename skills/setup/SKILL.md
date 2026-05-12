---
name: setup
description: Use when the user wants to install, reconfigure, or update their claude-personal-starter components. Walks them through choosing components via checkboxes and applies the changes via tools/install.
---

# /setup — claude-personal-starter

You are running the modular Claude starter setup. The user wants to pick (or re-pick) which components to install. The repo is cloned at `~/.claude-personal-starter/`. The installer CLI is at `~/.claude-personal-starter/tools/install`.

## Process

### 1. Refresh the source

Run:

```
git -C ~/.claude-personal-starter pull --ff-only
```

If it fails (no network, conflict), continue with whatever's on disk and tell the user.

### 2. Load the catalog

Run:

```
~/.claude-personal-starter/tools/install list-components --json
```

Parse the JSON. Group by `category`. Note which are `installed: true`.

### 3. Walk the user through each category

For each category, present the options via `AskUserQuestion`. Order: `safety`, `working-directory`, `tools`, `skills`, `identity`.

**Safety** (exclusive group — radio behavior, single-select):
- Question: "Pick a safety profile."
- Header: "Safety"
- multiSelect: false
- Options: one per safety component, with the component's `description` as the option description. Pre-select the currently-installed one (if any) or the `recommended: true` one as the first option.

**Working directory** (required):
- Question: "Where should your working directory be?"
- Default to `~/Work` if no answer. The agent can either state the default and proceed, or ask the user for an override via a free-text prompt.

**Tools** (multi-select, may need multiple questions if >4):
- Question: "Which tools do you want? (Tick all that apply.)"
- Header: "Tools"
- multiSelect: true
- Options: every component in the `tools` category. Pre-tick currently-installed.
- If more than 4 options, split into "Email tools" and "Calendar/Drive/Docs" sub-questions.

**Skills** (multi-select):
- Question: "Which workflow skills do you want?"
- Header: "Skills"
- multiSelect: true
- Options: every component in the `skills` category. Pre-tick installed.

**Identity** (single-select):
- Question: "Want to add a 'who I am' note to your CLAUDE.md?"
- Header: "Identity"
- multiSelect: false
- Options: ["Yes — describe me", "Skip — I'll edit CLAUDE.md myself later"]
- If "Yes," ask one follow-up open-ended question: "In a sentence or two, who are you and what do you mostly use Claude for?"

### 4. Compute diff

- `currently_installed` = set of installed ids from step 2.
- `requested` = union of every component the user ticked.
- `to_add` = `requested - currently_installed`
- `to_remove` = `currently_installed - requested`

### 5. Apply

Run:

```
~/.claude-personal-starter/tools/install apply \
  --add "<comma-separated to_add>" \
  --remove "<comma-separated to_remove>" \
  --working-dir "<path or omit>" \
  --identity-text "<text or omit>"
```

Show the output to the user.

### 6. Show post-install actions

For every newly-added component, read `~/.claude-personal-starter/tools/components/<id>/setup-notes.md` if it exists, and concatenate. Show the result as "Next steps:" — these are typically MCP `authenticate` commands the user needs to run in a fresh session.

### 7. Confirm

Print a one-line summary:

```
Done. Added: tool-gmail, skill-weekly-digest. Removed: (none). Currently installed: safety-strict, working-directory, identity-block, tool-gmail, tool-google-calendar, skill-email-triage, skill-weekly-digest.
```

## Edge cases

- **First-time install (nothing in manifest):** Treat every option as un-ticked. Proceed normally.
- **No `~/.claude-personal-starter/` directory:** Tell the user to re-run the curl bootstrap. Stop.
- **`tools/install` exits with a non-zero status:** Show stderr to the user, do not claim success.
- **User aborts via Ctrl-C in the middle:** Whatever has been applied via earlier `apply` calls is persistent; explain that re-running `/setup` will pick up where they left off.
