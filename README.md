# claude-personal-starter

A modular set of Claude Code recommendations. Pick what you want via an in-Claude checkbox UI; your agent applies the picks by editing your `~/.claude/CLAUDE.md`, `~/.claude/settings.json`, and copying any custom skills or hooks. No runtime, no package manager — your agent does the work using its normal tools.

## Install

You need Claude Code installed and authenticated already (via Anthropic's official install flow). Then:

```sh
curl -fsSL https://raw.githubusercontent.com/Tugboat-Solutions-Inc/claude-personal-starter/main/bootstrap.sh | sh
```

Then run `claude` and type `/setup`. The agent walks you through the picker.

## Update

Re-run `/setup` any time. It pulls the latest components from this repo and lets you add or remove pieces.

## What it sets up

Categories of components, all optional, all independently toggleable:

- **Safety** — strict (hooks block destructive shell + net egress; Write/Edit fenced) or chill (system writes denied, otherwise free)
- **Working directory** — sets your project home (default `~/Work`)
- **Identity** — one free-text "who I am" prompt, goes into your `CLAUDE.md`
- **Tools** — Gmail, Outlook (via Apple Mail), Google Calendar, plus more added later
- **Skills** — email triage, weekly digest

Cloud-tool components (Gmail, Calendar, etc.) point you at the official `authenticate` commands during install. We don't wrap them.

See `docs/components.md` for the catalog.

## What this is NOT

Not a package manager. Not a runtime. Not a wrapper around Claude Code itself. Just a curated set of CLAUDE.md fragments, settings recipes, hook scripts, and custom skills that your Claude agent applies when you tell it to. You own your `~/.claude/` directory.

## License

MIT. See `LICENSE`.
