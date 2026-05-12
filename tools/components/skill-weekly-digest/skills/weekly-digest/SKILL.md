---
name: weekly-digest
description: Use when the user wants a Monday-morning (or any-day) summary of the week — meetings, email volume, what's coming up, what fell behind.
---

# Weekly Digest

Build a single Markdown report covering the week from "today" to "today + 7 days," plus a brief look-back at "the last 7 days."

## Sections (in this order)

```
## Week of <Monday date>

### This week's meetings (next 7 days)
<bulleted list, day-grouped, with title + time + attendees>

### Inbox status
- <N> unread messages, of which <urgent count> look time-sensitive (run /email-triage for detail)
- People waiting on a reply: <list anyone who's emailed twice without a response>

### Loose ends from last week
- <items that look unresolved — replies you started drafting but didn't send, calendar events you cancelled with "rescheduling later," etc.>

### Things to think about
- <2-3 themes the AI noticed across the week — e.g., "you spent 60% of last week in internal meetings; only 2 customer calls">
```

## Rules

- **Don't make stuff up.** If you can't determine "loose ends" from real data, omit that section.
- **Look at the calendar AND email together.** A meeting that got rescheduled twice has email context that matters.
- **Quantify when you can** — "8 hours of meetings this week" is more useful than "lots of meetings."
- **Don't draft action items.** This is a digest, not a planner. The user will ask separately if they want followups.
