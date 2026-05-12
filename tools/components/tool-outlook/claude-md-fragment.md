## Outlook (via Apple Mail)

The user's Microsoft 365 mailbox is synced to Apple Mail. You can:

- **Read** by grepping ~/Library/Mail/.../*.emlx files directly, or via `mdfind` (Spotlight).
- **Search structured** via `osascript -e 'tell application "Mail" ...'` — read messages by ID, list messages in inbox, etc.
- **Draft replies** by creating a Mail.app draft via AppleScript. Never auto-send.

Pattern: draft → show preview → wait for explicit "send" → ask the user to click send manually. Auto-send is not enabled by design.

If the user reports Apple Mail isn't syncing, the fix is in System Settings → Internet Accounts. Don't try to fix it via Claude.
