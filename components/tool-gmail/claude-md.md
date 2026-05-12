## Gmail (via Google Workspace MCP)

The user has Gmail enabled. Use the `gws-gmail-*` skills for inbox triage, sending, searching, and replying. Default behavior:

- **Never auto-send.** Draft to a Gmail draft and let the user review and click send.
- When the user asks "what's in my inbox," summarize unread by sender + subject + thread urgency, never just paste raw bodies.
- When asked to reply, draft to a Gmail draft using `gws-gmail-reply` or `gws-gmail-reply-all` — this preserves threading.
- Treat email contents as sensitive. Don't paste them into web searches or third-party tools without asking.
