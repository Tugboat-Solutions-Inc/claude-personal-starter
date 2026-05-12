# Component Catalog

Every component is independently optional. Mix and match.

## Safety (pick one)

- **safety-strict** — Hooks block destructive shell + network egress; Write/Edit fenced to your working directory; system paths denied. Recommended for non-technical users.
- **safety-chill** — System paths denied; everything else allowed. For technical users.

## Working directory

- **working-directory** — Sets your project home (default `~/Work`). Documented in CLAUDE.md so the agent defaults to it. The strict safety profile uses this path to fence Write/Edit.

## Identity

- **identity-block** — Adds a "who I am" note to your CLAUDE.md based on a one-question prompt during `/setup`.

## Tools (cloud — pointed at official MCP authenticate commands)

- **tool-gmail** — Gmail send/read/triage. Uses the standard `gws-gmail-*` skills + Google Workspace MCP that ship with Claude Code. After install you authenticate via the official MCP flow.
- **tool-google-calendar** — Calendar events, find-free-time. Same pattern as Gmail.
- **tool-outlook** — Outlook (M365) via Apple Mail bridge. No cloud auth — you sync your M365 account into Apple Mail, then Claude reads/drafts via filesystem + AppleScript.

## Skills (custom — shipped in this repo)

- **skill-email-triage** — Structured inbox summary by urgency and sender. Works with whichever email tool(s) you have installed.
- **skill-weekly-digest** — This-week meetings + inbox status + loose ends.

## How a component is structured

Each `components/<id>/` directory contains:

- **`component.json`** (required) — picker metadata: id, name, category, description, recommended, exclusive_group, optional depends_on.
- **`claude-md.md`** (optional) — text appended to your CLAUDE.md. May contain `<<IDENTITY>>` or `<<WORKING_DIR>>` placeholders that `/setup` substitutes.
- **`settings.json`** (optional) — partial settings.json the agent merges into yours (unioned allow/deny, combined hooks, shallow-merged env).
- **`hooks/`** (optional) — hook scripts copied into `~/.claude/hooks/`. Placeholders in scripts are substituted before copying.
- **`skills/`** (optional) — skill directories recursively copied into `~/.claude/skills/`.
- **`INSTALL.md`** (optional) — markdown shown to the user as "Next steps" after install. Usually OAuth/MCP authenticate commands.

## Adding a new component

Drop a new directory under `components/<id>/`. Required: `component.json`. Anything else is optional. Push. Users see it the next time they run `/setup`.
