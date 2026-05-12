# Onboarding

The whole thing takes about 30 minutes if Claude Code isn't installed yet, or 5 minutes if it is.

## Step 1 — Install Claude Code (skip if you already have it)

Claude Code is Anthropic's CLI for Claude. Install it:

```sh
curl -fsSL https://claude.ai/install.sh | sh
```

Then start it once to log in:

```sh
claude
```

It will open a browser for OAuth. After you sign in, **press Enter** on the success page in the Terminal (if you skip that, the credential isn't saved). Then type `/exit`.

## Step 2 — Run the bootstrap

```sh
curl -fsSL https://raw.githubusercontent.com/Tugboat-Solutions-Inc/claude-personal-starter/main/bootstrap.sh | sh
```

This clones the repo to `~/.claude-personal-starter/` and drops a `/setup` skill into `~/.claude/skills/setup/`. Nothing else changes yet.

## Step 3 — Pick your components

```sh
claude
```

Type `/setup` and walk through the checkboxes.

## Step 4 — Run any post-install actions

After `/setup` finishes, it shows "Next steps:" — usually one or two commands to authenticate Google services. Run them in a new Claude session.

## Step 5 — Try it

Restart Claude (so `~/.claude/CLAUDE.md` reloads) and ask:

- "What's in my inbox today?"
- "What's on my calendar this week?"
- "Give me a weekly digest."

## To update later

Re-run `/setup` any time. It pulls the latest components from GitHub and lets you tick/untick.

## To reset

Edit or delete `~/.claude/CLAUDE.md`, `~/.claude/settings.json`, or the `~/.claude/skills/*` and `~/.claude/hooks/*` files directly. The manifest is at `~/.claude/.claude-personal-starter.json`.
