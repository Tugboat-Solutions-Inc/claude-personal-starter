---
name: email-triage
description: Use when the user wants a structured summary of unread email, broken down by urgency, sender, and theme. Works against Gmail (via gws-gmail), Outlook (via Apple Mail), or both if available.
---

# Email Triage

Detect which email backends are available:

1. **Gmail** — try `gws-gmail-watch` or `mcp__claude_ai_Gmail__*` tools. If they return data, Gmail is available.
2. **Apple Mail (Outlook/iCloud)** — check whether `~/Library/Mail` exists and contains accounts. If yes, Apple Mail is available.

If both, run both and merge. If neither, tell the user no email backend is configured and point at `/setup`.

## Output structure

Produce a single Markdown block with these sections (omit sections that have no items):

```
### Urgent (anything time-sensitive in next 24h)
- **<sender>** — <subject> · <one-line summary>

### From people you usually reply to fast
- **<sender>** — <subject> · <one-line summary>

### Newsletters / automated
- count: N — skipping detail; mention any that look unusual.

### Promotional / can ignore
- count: N
```

## Rules

- **Never draft replies in this skill.** Triage only. The user will say "reply to the Acme one" separately.
- **Group automated email aggressively.** Most inboxes are 80% noise. Don't list every newsletter — just count them.
- **Identify urgency by content, not sender.** A meeting reschedule from a colleague today is more urgent than a partner asking about a Q3 plan.
- **Read only what's necessary** to summarize. Don't paste full email bodies into your output unless the user asks.
