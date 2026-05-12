# Component Catalog

Every component is independently optional. Mix and match.

## Safety (pick one)

- **safety-strict** — Hooks block destructive shell + network egress; Write/Edit fenced to your working directory; system paths denied.
- **safety-chill** — System paths denied; everything else allowed.

## Working directory

- **working-directory** — Sets your project home (default `~/Work`).

## Identity

- **identity-block** — Adds a one-line "who I am" note to your CLAUDE.md.

## Tools

- **tool-gmail** — Gmail send/read/triage via Google Workspace MCP.
- **tool-google-calendar** — Calendar events, find-free-time.
- **tool-outlook** — Outlook (M365) via Apple Mail bridge.

## Skills

- **skill-email-triage** — Structured inbox summary by urgency and sender.
- **skill-weekly-digest** — This-week meetings + inbox status + loose ends.

## Adding more

To add a component, drop a directory under `tools/components/<id>/` containing `component.json`, `version.txt`, and any of `claude-md-fragment.md`, `settings-fragment.json`, `skills/`, `hooks/`, `agents/`, `setup-notes.md`. Bump and PR.
