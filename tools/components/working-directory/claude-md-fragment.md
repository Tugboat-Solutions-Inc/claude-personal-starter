## Working directory

The user has chosen a working directory for project files. Default and read it from the manifest at `~/.claude/.claude-personal-starter.json` under `working_directory`. Treat that path as the home base for everything the user is actively working on.

When the user says "put this somewhere" or "open my notes," default to that directory. Don't write outside it without asking first.
