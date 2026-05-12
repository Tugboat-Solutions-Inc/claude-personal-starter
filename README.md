# claude-personal-starter

A modular Claude Code starter. Pick the pieces you want via an in-Claude checkbox UI. Reconfigure any time.

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/Tugboat-Solutions-Inc/claude-personal-starter/main/bootstrap.sh | sh
```

Then run `claude` and type `/setup`.

## Update

Re-run `/setup` any time. It pulls the latest components and lets you add or remove pieces.

## What it sets up

Categories of components, all optional, all independently toggleable:

- **Safety** — strict (hooks block destructive shell and net egress) or chill (system writes denied, otherwise free)
- **Tools** — Gmail, Outlook, Google Calendar, Google Docs, Google Drive, Google Sheets, Google Slides, Google Tasks, macOS Calendar / Contacts, Linear, Stripe
- **Skills** — email triage, weekly digest, meeting prep, folder summary, doc drafting
- **Identity** — one free-text prompt about who you are; goes into your `CLAUDE.md`

See `docs/components.md` for the catalog.

## License

MIT. See `LICENSE`.
