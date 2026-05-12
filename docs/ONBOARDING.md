# Onboarding

Assumes you have a Mac. About 30 minutes start to finish if Claude Code isn't installed yet, or 5 minutes if it is.

## Step 1 — Install Claude Code through the official path

Skip if you already have it.

```sh
curl -fsSL https://claude.ai/install.sh | sh
```

Then start it once and OAuth-log in:

```sh
claude
```

After signing in in the browser, **press Enter** on the success page in the Terminal — if you skip that, the credential isn't saved. Type `/exit` to close.

## Step 2 — Run the bootstrap

```sh
curl -fsSL https://raw.githubusercontent.com/Tugboat-Solutions-Inc/claude-personal-starter/main/bootstrap.sh | sh
```

This clones the repo to `~/.claude-personal-starter/` and drops a `/setup` skill into `~/.claude/skills/setup/`. Nothing else changes.

## Step 3 — Pick your components

```sh
claude
```

Type `/setup` and walk through the checkboxes. The agent will:

1. Ask which safety profile you want.
2. Ask where your working directory should be.
3. Ask which tools you use (Gmail, Outlook, Calendar, etc.).
4. Ask which workflow skills you want.
5. Ask if you want a "who I am" identity block.
6. Apply your picks to `~/.claude/CLAUDE.md`, `~/.claude/settings.json`, `~/.claude/hooks/`, and `~/.claude/skills/`.
7. Show you any post-install commands (typically MCP `authenticate` commands for cloud tools).

## Step 4 — Run any post-install commands

Cloud tools like Gmail and Calendar need OAuth. Whatever `/setup` printed under "Next steps" — go run those in a fresh Claude session. They use Anthropic's official MCP auth flow.

## Step 5 — Restart Claude

After the configuration changes, exit and restart Claude so it picks up the new `~/.claude/CLAUDE.md` and `settings.json`. Then try:

- "What's in my inbox today?"
- "What's on my calendar this week?"
- "Give me a weekly digest."

## To update later

Re-run `/setup` any time. It pulls the latest components and lets you tick/untick.

## To reset

Edit or delete `~/.claude/CLAUDE.md`, `~/.claude/settings.json`, or anything in `~/.claude/skills/` and `~/.claude/hooks/`. There's no manifest or lockfile to keep in sync.
