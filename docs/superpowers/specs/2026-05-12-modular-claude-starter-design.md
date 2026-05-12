# Modular Claude Starter — Design (v2)

**Status:** Approved (design phase)
**Author:** Aaron
**Date:** 2026-05-12
**Supersedes:** v1 (recommendation-set rewrite — see git history for the over-engineered runtime version)

---

## Problem

Aaron has Claude Code patterns that several different audiences would benefit from (personal-use friends, Tugboat employees, attorneys via the existing attorney-claude-starter). He wants to share those patterns without:

- Maintaining a runtime that owns the user's `~/.claude/` directory.
- Bundling Claude Code itself, OAuth flows, MCP server installs, or any official Anthropic install path.
- Tracking what's installed, deep-merging settings, or otherwise pretending to be a package manager.

## Goal

A repo of **recommendations** the user's own Claude agent applies. The user installs Claude Code through the official Anthropic flow, runs `claude`, types `/setup`, and the agent walks them through a checklist of optional configuration pieces. The agent then edits the user's `~/.claude/CLAUDE.md`, `~/.claude/settings.json`, copies any custom skills, and tells the user which official commands to run for OAuth / MCP setup. From there the user iterates with their agent.

## Non-Goals

- No Python CLI, no manifest, no version tracking, no contribution-tracking-for-undo, no end-to-end install/remove orchestration. The agent applies recommendations using its existing Read/Edit/Bash tools; the user re-runs `/setup` to change their mind.
- No official-install wrapping. Claude Code OAuth, MCP server installation, Google Workspace authentication, etc. — all handled through the user's normal Claude tooling and Anthropic-provided commands. We just point at them.
- No personas or presets. Pure modular checklist.

## Architecture

```
github.com/Tugboat-Solutions-Inc/claude-personal-starter
├── bootstrap.sh                  ← curl entry point: clone repo + drop /setup skill
├── components/                   ← every recommendation lives here
│   ├── safety-strict/
│   │   ├── component.json        ← picker metadata: id, name, category, description, recommended, exclusive_group
│   │   ├── claude-md.md          ← text to add to user's CLAUDE.md (optional)
│   │   ├── settings.json         ← settings to merge into user's settings.json (optional)
│   │   ├── hooks/                ← hook scripts to copy into ~/.claude/hooks/ (optional)
│   │   └── INSTALL.md            ← post-install commands the user/agent runs (optional)
│   ├── tool-gmail/
│   │   ├── component.json
│   │   ├── claude-md.md
│   │   └── INSTALL.md            ← e.g., "run @claude_ai_Gmail authenticate"
│   ├── skill-email-triage/
│   │   ├── component.json
│   │   ├── claude-md.md
│   │   └── skills/
│   │       └── email-triage/SKILL.md
│   └── ... (and so on)
├── skills/
│   └── setup/SKILL.md            ← the in-Claude TUI driver
├── docs/
│   ├── ONBOARDING.md
│   └── components.md
├── LICENSE
├── README.md
└── .gitignore
```

**Two-stage install:**

1. **Bootstrap.** One curl line. Clones the repo to `~/.claude-personal-starter/`, copies `skills/setup/SKILL.md` into `~/.claude/skills/setup/`. Nothing else.
2. **`/setup`.** The user runs `claude`, types `/setup`. The skill instructions tell the agent to:
   - `git pull` the repo for any updates.
   - List components by reading `components/*/component.json`.
   - Group by category and present checkboxes via `AskUserQuestion`.
   - For each picked component, apply it using normal Read/Edit/Bash tools.
   - Show the concatenated `INSTALL.md` content as "next steps" (commands the user runs in a fresh Claude session, like Gmail OAuth).

## Component Schema

```
components/<id>/
├── component.json    REQUIRED — picker metadata
├── claude-md.md      OPTIONAL — content to append to CLAUDE.md (with optional <<PLACEHOLDERS>>)
├── settings.json     OPTIONAL — partial settings to merge
├── hooks/            OPTIONAL — files to copy into ~/.claude/hooks/
├── skills/           OPTIONAL — directories to copy into ~/.claude/skills/
└── INSTALL.md        OPTIONAL — markdown shown to user as post-install steps
```

`component.json`:

```json
{
  "id": "tool-gmail",
  "name": "Gmail",
  "category": "tools",
  "description": "Send, read, search, and triage Gmail. Uses the standard Google Workspace MCP that ships with Claude Code; no skills are bundled here. After install you run the Gmail authenticate command from a fresh session.",
  "recommended": false,
  "exclusive_group": null
}
```

Categories used: `safety`, `working-directory`, `identity`, `tools`, `skills`. New categories are fine — the picker just groups by whatever it finds.

`exclusive_group` non-null means radio behavior in the picker (pick one).

## Placeholder substitution

Two known placeholders the `/setup` skill substitutes before writing CLAUDE.md:

- `<<IDENTITY>>` — replaced with the user's free-text answer to "who are you, what do you mostly use this for?"
- `<<WORKING_DIR>>` — replaced with the working directory path the user picked (default `~/Work`).

For hooks, the same `<<WORKING_DIR>>` substitution applies before copying. (The strict-safety hook needs to know which directory to fence Write/Edit to, and we don't ship a manifest for it to read at runtime.)

## How `/setup` applies a component

This is the heart of the system. The SKILL.md is one document of instructions the agent follows. For each picked component, the agent:

1. **CLAUDE.md edit.** Reads `components/<id>/claude-md.md`. Substitutes placeholders. Reads the user's `~/.claude/CLAUDE.md` (or treats absent as empty). If a section header from the fragment already exists, replaces that section; otherwise appends to the end. The agent uses Read + Edit, no parser library.
2. **settings.json merge.** Reads `components/<id>/settings.json`. Reads user's `~/.claude/settings.json` (or initializes from a base if absent). Unions `permissions.allow` and `permissions.deny` arrays. Combines `hooks` by matcher + command. Shallow-merges `env`. Writes back. The agent does this manually using Read + parsing JSON in its head + Write.
3. **Hooks copy.** Reads each file in `components/<id>/hooks/`. Substitutes `<<WORKING_DIR>>` if present. Writes to `~/.claude/hooks/<filename>`. Marks executable.
4. **Skills copy.** Recursively copies `components/<id>/skills/` into `~/.claude/skills/`.
5. **INSTALL.md.** Concatenates with notes from other newly-applied components. Shown to the user at the end as "Next steps."

The agent may make small judgment calls (e.g., "your settings.json doesn't have a `permissions` key yet, I'm adding it"). That's fine — that's the whole point of having an agent do it instead of a Python script.

## Removing a component

Re-running `/setup` and unticking a previously-picked component is the removal path. The agent reads the component to know what it added (the section header in CLAUDE.md, the entries in settings.json, the file paths in hooks/skills) and removes those. No manifest needed because the agent is smart enough to look at both the component definition and the user's current state.

## Bootstrap

`bootstrap.sh`:

1. Verify `git` and `claude` are on PATH.
2. Clone `https://github.com/Tugboat-Solutions-Inc/claude-personal-starter.git` to `~/.claude-personal-starter/` (or `git pull` if it already exists).
3. Copy `skills/setup/SKILL.md` into `~/.claude/skills/setup/SKILL.md`.
4. Print "Run `claude` then type `/setup`."

That's it. Nothing else gets installed.

## Update flow

- New component released → `git pull` (run by `/setup` on next invocation) → user sees the new option in the picker.
- Component contents changed → user re-ticks it via `/setup` → agent re-applies.
- Component removed from catalog → existing installations keep working; the picker just doesn't show it.

## Initial component set (v2)

Same nine as v1, restructured under the new shape:

- **Safety** (`exclusive_group: "safety"`): `safety-strict`, `safety-chill`
- **Working directory**: `working-directory`
- **Identity**: `identity-block`
- **Tools**: `tool-gmail`, `tool-google-calendar`, `tool-outlook`
- **Skills**: `skill-email-triage`, `skill-weekly-digest`

## What this is NOT

- **Not a package manager.** No version pinning, dependency graph, lockfile, or update notifications.
- **Not a runtime.** Nothing runs in the background. The agent applies things and goes away.
- **Not a wrapper around Claude Code.** Anthropic owns Claude Code installation, OAuth, and the official MCP install paths. We just hand off.
- **Not a bundle for non-technical users.** It assumes the user has already installed Claude Code and authed. If they need a fully wrapped one-double-click install, that's `pi-agent-bundle`'s job — separate product, separate audience.

## Distribution

- **Repo:** `Tugboat-Solutions-Inc/claude-personal-starter`. Public. MIT.
- **Curl:** `curl -fsSL https://raw.githubusercontent.com/Tugboat-Solutions-Inc/claude-personal-starter/main/bootstrap.sh | sh`
- **Updates:** standard `git pull`, surfaced via re-running `/setup`.
- **No telemetry.** Aaron has no idea who installed it unless they tell him.
