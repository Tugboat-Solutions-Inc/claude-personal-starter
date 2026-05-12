# Modular Claude Code Starter — Design

**Status:** Approved (design phase)
**Author:** Aaron
**Date:** 2026-05-12

---

## Problem

Aaron has a Claude Code setup that does a lot of useful work (Gmail triage, Google Workspace flows, Tugboat business work, dev workflows). Several different people would benefit from chunks of it:

- **Personal-use friends** ("Chris-types") — want the general personal-assistant pieces (Gmail, Calendar, Docs, weekly digest), nothing Tugboat or dev.
- **Tugboat employees** — want personal pieces plus Tugboat business context (brand voice, claims terminology, Linear), no dev stack.
- **Tugboat developers** — already served by `tugboat-tools` (Michael Riffle's git-pull installer), no new work needed.
- **Specialized variants** like `attorney-claude-starter` for Cameron's dad — same skeleton, domain-specific overlay.

The existing pieces don't compose. `pi-agent-bundle` is a zip with the Pi runtime; `attorney-claude-starter` is a hand-delivered folder; `tugboat-tools` is git-managed but Tugboat-internal. None of them let someone say "I use Gmail and Calendar but not Outlook, give me strict safety, skip the Tugboat stuff."

## Goal

A single public repo, installable via one curl line, that lets any user pick exactly which components they want via an in-Claude checkbox interface. Updates flow through git pull. Users can rerun setup any time to add or remove components.

## Non-Goals

- No personas, presets, or "I'm a {role}" shortcuts. The picker is the interface; users tick what they want.
- No TUI library (`gum`, `whiptail`, `dialog`). Claude itself is the TUI via `AskUserQuestion`.
- No bundling of the Pi runtime, Claude Code installer, or Anthropic auth. The bootstrap assumes Claude Code is already installed and authenticated.
- No replacement for `tugboat-tools`. Developers continue using that. This starter is for non-dev users.

## High-Level Architecture

```
github.com/<org>/claude-personal-starter
├── bootstrap.sh                  ← curl … | sh entry point
├── tools/
│   ├── install.sh                ← git-pull installer with versioned components + manifest (adapted from tugboat-tools)
│   └── components/               ← every available component lives here
│       ├── safety-strict/
│       ├── safety-chill/
│       ├── tool-outlook/
│       ├── tool-gmail/
│       ├── tool-google-calendar/
│       ├── …
│       ├── skill-email-triage/
│       ├── skill-weekly-digest/
│       └── …
├── skills/
│   └── setup/                    ← the in-Claude TUI
│       └── SKILL.md
├── docs/
│   ├── ONBOARDING.md             ← getting Claude Code installed (curl + OAuth), then run /setup
│   └── components.md             ← human-readable catalog of every component
└── README.md
```

**Two-stage install:**

1. **Bootstrap** (one curl line). Drops the `setup` skill into `~/.claude/skills/setup/` and nothing else. Idempotent.
2. **In-Claude setup** (`/setup`). The skill uses `AskUserQuestion` to present the picker. It then runs `tools/install.sh install --components <list>` to apply the chosen components.

Subsequent re-runs of `/setup` read the manifest to show current state and let the user add/remove components. `git pull` followed by `tools/install.sh upgrade` brings in new component versions without touching the user's selection.

## Component Model

A component is a self-contained directory under `tools/components/<name>/`:

```
tools/components/tool-gmail/
├── component.json                ← metadata
├── version.txt                   ← semver
├── claude-md-fragment.md         ← optional — block to append/merge into ~/.claude/CLAUDE.md
├── settings-fragment.json        ← optional — JSON to deep-merge into ~/.claude/settings.json
├── hooks/                        ← optional — files to copy into ~/.claude/hooks/
├── skills/                       ← optional — skill directories to copy into ~/.claude/skills/
├── agents/                       ← optional — agent files to copy into ~/.claude/agents/
└── setup-notes.md                ← optional — shown to the user after install ("now run X to finish setup")
```

**`component.json` schema:**

```json
{
  "id": "tool-gmail",
  "name": "Gmail",
  "category": "tools",
  "description": "Send, read, search, and triage Gmail via Google MCP. Installs Google Workspace skills (gws-gmail-*) and configures the MCP server.",
  "recommended": false,
  "exclusive_group": null,
  "depends_on": [],
  "conflicts_with": [],
  "post_install_action_required": "Run /authenticate google-workspace to authorize Gmail access."
}
```

Fields:

- `category` — `safety`, `working-directory`, `tools`, `skills`, `identity`. Used to group in the picker.
- `recommended` — true means pre-checked in the picker. Used for things like the destructive-command deny list.
- `exclusive_group` — non-null means "pick at most one in this group" (radio behavior). The two safety profiles share `"exclusive_group": "safety"`.
- `depends_on` / `conflicts_with` — referential integrity. If you tick `skill-weekly-digest` it auto-ticks `tool-google-calendar`.

**Identity block:** the "Who you are" CLAUDE.md section is treated as a special component (`identity-block`) that, when ticked, prompts the user with one open-ended question via `AskUserQuestion` and writes the answer verbatim into a labeled block in `CLAUDE.md`. Skippable; editable later via `/setup`.

## CLAUDE.md Composition

`~/.claude/CLAUDE.md` is assembled from component fragments using labeled markers, similar to the `tugboat-tools` managed-import pattern:

```markdown
# >>> claude-personal-starter: identity — managed, edit between markers
<identity content from /setup prompt or user edits>
# <<< claude-personal-starter: identity

# >>> claude-personal-starter: safety-strict — managed, regenerated by /setup
<strict safety doctrine fragment>
# <<< claude-personal-starter: safety-strict

# >>> claude-personal-starter: tool-gmail — managed, regenerated by /setup
<Gmail tool notes fragment>
# <<< claude-personal-starter: tool-gmail
```

- Content **between markers** is regenerated by `/setup`. Users should not edit it; their edits will be lost on the next run.
- Exception: the `identity` block. Users are expected to edit it. `/setup` only writes it if it is empty.
- Content **outside any markers** is never touched by `/setup`. Users can add their own freeform sections at the top or bottom of the file.

`tools/install.sh` is responsible for parsing the existing file, removing managed blocks for components the user is removing, inserting blocks for components the user is adding, and leaving everything else alone.

## settings.json Composition

`~/.claude/settings.json` is a deep-merge of every selected component's `settings-fragment.json`, plus a base file:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "auto",
    "allow": [],
    "deny": []
  },
  "hooks": {},
  "env": {}
}
```

- `defaultMode: "auto"` is set by the base file regardless of safety profile. The deny list and hooks enforce safety; auto mode is a UX default that prevents prompting on allowlisted tools.
- `permissions.allow` and `permissions.deny` are unioned across components.
- `hooks.PreToolUse` (etc.) are merged by matcher.
- `env` is shallow-merged; later components override earlier ones for the same key (but this should be rare).

If the user already has a `~/.claude/settings.json`, `tools/install.sh` reads it, removes the managed components' contributions (tracked by id in the manifest), adds the new ones, writes back. Anything the user added manually outside the managed fields is preserved.

## Categories and Initial Components

These are the components shipped in v1. New ones are added by dropping a directory under `tools/components/` and bumping the catalog.

### Safety (exclusive group — pick one)

Members of the `"exclusive_group": "safety"` group. v1 ships two; new safety profiles (e.g., `safety-attorney`) can be added later by dropping in another component with the same exclusive group.

- **`safety-strict`** — Hooks block destructive commands (`rm -rf`, `sudo`, force pushes, hard resets, `defaults write`, `launchctl`, `diskutil`, `security`). Hooks block network egress (`curl`, `wget`, `scp`, `rsync`). Working-directory hook fences Write/Edit to the chosen working directory. System paths (`/etc`, `/Library`, `/System`, `/usr`, `~/Library`) denied for Write/Edit. Recommended for non-technical users.
- **`safety-chill`** — System paths denied for Write/Edit (same as strict). Destructive shell commands not blocked. Network egress allowed. No working-directory fence. Recommended for technical users who want freedom.

### Working directory

- **`working-directory`** — Required component. Prompts for a path (default `~/Work/`). Creates the directory if it doesn't exist. Adds a marker block to CLAUDE.md naming the convention. `safety-strict`'s hook uses this path; `safety-chill` ignores it.

### Tools

Each tool is independent. Tick what you have/use:

- **`tool-outlook`** — Installs Apple Mail AppleScript helpers for reading/drafting against an M365 mailbox synced to Mail.app. Adds an allowlist for `osascript -e 'tell application "Mail"...'`.
- **`tool-icloud-mail`** — Same Apple Mail bridge, framed for iCloud Mail users.
- **`tool-gmail`** — Adds Google Workspace MCP + `gws-gmail-*` skills (send, read, triage, watch, reply, reply-all, forward). Requires post-install OAuth.
- **`tool-google-calendar`** — Adds `gws-calendar` skills + MCP. Post-install OAuth.
- **`tool-google-drive`** — Adds `gws-drive` skills + MCP. Post-install OAuth.
- **`tool-google-docs`** — Adds `gws-docs` skills.
- **`tool-google-sheets`** — Adds `gws-sheets` skills.
- **`tool-google-slides`** — Adds `gws-slides` skills.
- **`tool-google-tasks`** — Adds `gws-tasks` skills.
- **`tool-macos-calendar`** — AppleScript helpers for Calendar.app + Contacts.app (M365 or iCloud).
- **`tool-linear`** — Installs the `linear` skill. Requires `LINEAR_API_KEY`.
- **`tool-stripe`** — Installs Stripe MCP. Requires Stripe API key.

### Skills

Workflow patterns that compose multiple tools:

- **`skill-email-triage`** — Unread inbox summary by sender/subject/urgency. Works with any email tool ticked. (Generalizes `attorney-claude-starter/skills/email-triage`.)
- **`skill-weekly-digest`** — Weekly summary of meetings + unread email count. Requires `tool-gmail` + `tool-google-calendar` (or Outlook/macOS equivalents).
- **`skill-meeting-prep`** — Agenda + attendees + linked docs for the next meeting. Requires `tool-google-calendar` + `tool-google-drive` or `tool-google-docs`.
- **`skill-folder-summary`** — Summarize a project folder into a structured `NOTES.md`. (Generalizes `case-file-summary`.) No tool dependency.
- **`skill-doc-drafting`** — Draft Google Docs from prompts using Aaron's tone-of-voice patterns. Requires `tool-google-docs`.

### Identity

- **`identity-block`** — Prompts once for a free-text "who are you, what do you do, what do you mostly use this for" answer. Inserts it verbatim into the CLAUDE.md `identity` managed block. Skippable. Editable later.

## The `/setup` Skill

A skill at `~/.claude/skills/setup/SKILL.md`. When invoked:

1. **Read state.** Check `~/.claude/.claude-personal-starter.json` (the manifest) for already-installed components. If absent, treat as fresh install.
2. **Refresh source.** `git -C ~/.claude-personal-starter pull` (the cloned repo lives there; bootstrap puts it in place). Skip with `--offline` flag.
3. **Show categories in order.** For each category:
   - Read all `component.json` files in `tools/components/` belonging to that category.
   - Present them via `AskUserQuestion`. Use `multiSelect: true` except for `exclusive_group` categories.
   - Pre-tick already-installed and `recommended: true` components.
   - Show description as the option's `description`.
4. **Apply changes.** Compute the diff (added / removed / unchanged). Call `tools/install.sh apply --add <list> --remove <list>`. The script:
   - For each removed component: remove its CLAUDE.md block, settings fragment, hooks, skills.
   - For each added component: append CLAUDE.md block, deep-merge settings, copy hooks/skills/agents.
   - Update the manifest.
5. **Handle the identity block.** If `identity-block` is selected and the existing identity block is empty, ask the open-ended question. If non-empty, leave it alone (user has edited it).
6. **Show post-install actions.** Concatenate `setup-notes.md` from every newly added component. Common case: a Google Workspace tool tells the user to start a new Claude session and run the corresponding `authenticate` MCP tool (e.g., `mcp__claude_ai_Gmail__authenticate`) to authorize access. Exact command is per-component; the spec does not prescribe it.
7. **Confirm.** Show a summary: what was added, what was removed, what's now installed. Done.

## Bootstrap Script

`bootstrap.sh` is the curl-able entry point. Hosted on the repo's `main` branch via raw GitHub URL or on a stable redirect. It:

1. Verifies Claude Code is installed (`command -v claude`). Errors with install instructions if not.
2. Verifies the user is authenticated (`claude --help` works without OAuth flow).
3. Clones the repo to `~/.claude-personal-starter/` (or pulls if it exists).
4. Copies `skills/setup/` into `~/.claude/skills/setup/`.
5. Prints: "Setup skill installed. Run `claude` and type `/setup` to pick your components."

That's it. The bootstrap does not configure anything else. All real configuration happens in `/setup`.

## Update Flow

- **New component released.** Aaron pushes to the repo. Users run `/setup`; the skill does `git pull` first, then presents the picker with the new component visible.
- **Component upgraded.** Bump `version.txt`. Users run `/setup` and tick "upgrade installed components" — the skill detects version drift and reapplies the new fragments.
- **Component removed from the catalog.** Existing installations keep working; the picker just doesn't show it. Aaron's responsibility not to break the schema.

## Distribution

- **Repo:** public, `Tugboat-Solutions-Inc/claude-personal-starter`. Public license (MIT). Anyone can fork.
- **Curl line:** `curl -fsSL https://raw.githubusercontent.com/Tugboat-Solutions-Inc/claude-personal-starter/main/bootstrap.sh | sh`
- **Updates:** standard git pull, surfaced through `/setup` re-runs.
- **No telemetry, no callbacks, no per-user tracking.** Aaron has no idea who's installed it unless they tell him.

## How This Subsumes Existing Bundles

- **`attorney-claude-starter`** — Becomes an overlay repo (or a set of optional components like `safety-attorney`, `tool-westlaw-stub`, `skill-demand-letter-draft`, `skill-medical-timeline`) that lives in this same repo or a sibling. The four legal-specific skills convert to components; the strict-safety profile + attorney CLAUDE.md doctrine becomes `safety-attorney` (an exclusive-group sibling of `safety-strict` and `safety-chill`).
- **`pi-agent-bundle`** — Separate product. It bundles the Pi runtime for non-technical Tugboat users with zero CLI experience. This starter assumes Claude Code is already installed. The two don't compete; pi-agent-bundle could eventually be retired by adding a Pi-runtime bootstrap shim to this starter, but that's a future decision.
- **`tugboat-tools`** — Stays as-is for Tugboat developers. The personal starter could ship `tool-tugboat-team` and `tool-tugboat-claims` components that overlap with what's in tugboat-tools, but the dev-only skills (platform-architecture, schema-and-data, ai-and-integrations) stay in tugboat-tools.

## Open Questions (resolved or deferred)

- **Component versioning across user installs.** Deferred. v1 uses simple "latest in main" semantics. If a user wants a pinned version, they can clone a specific tag.
- **Cross-platform.** v1 is macOS-only. Apple Mail and AppleScript tools are macOS-specific. Hooks are Python (cross-platform). Linux support deferred to v2.
- **MCP server installation.** The tool components reference MCP servers. v1 assumes the user installs MCPs separately via `claude mcp add`. The components only install skills and configure allowlists. Future: have `tool-gmail` etc. invoke `claude mcp add google-workspace` during install.

## Implementation Plan (high level)

1. Repo scaffold + bootstrap script.
2. `tools/install.sh` — adapted from `tugboat-tools/tools/install.sh`. Handles CLAUDE.md block parsing, settings.json deep-merge, manifest tracking.
3. `skills/setup/SKILL.md` — the in-Claude TUI driver.
4. Initial component set — safety-strict, safety-chill, working-directory, identity-block, plus two or three tools (gmail, google-calendar, outlook) and two skills (email-triage, weekly-digest) to validate the pattern end-to-end.
5. Fill in remaining components iteratively. Each is small (a fragment, a skill or two, maybe a hook) and follows the same template.
6. `attorney-claude-starter` migration: convert its four skills and safety doctrine into components in this repo, mark the existing folder as superseded.

Detailed plan to follow via writing-plans skill.
