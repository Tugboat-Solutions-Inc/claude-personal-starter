## Outlook post-install

1. Open System Settings → Internet Accounts → Add Account → Microsoft Exchange.
2. Sign in with your work email. Microsoft handles OAuth + 2FA.
3. When asked which apps to enable, tick Mail (Calendar / Contacts optional).
4. Open Mail.app and let it download messages to ~/Library/Mail (~1 hour for a typical mailbox).
5. In Terminal.app preferences → Privacy & Security, ensure Terminal has **Full Disk Access** so Claude can read mailbox files.

You can keep using Outlook as your everyday client. Apple Mail runs in the background as Claude's read window.
