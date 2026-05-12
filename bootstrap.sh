#!/usr/bin/env bash
# claude-personal-starter bootstrap.
#
# Usage: curl -fsSL https://raw.githubusercontent.com/Tugboat-Solutions-Inc/claude-personal-starter/main/bootstrap.sh | sh
#
# What it does: clones the repo to ~/.claude-personal-starter/ and drops the
# /setup skill into ~/.claude/skills/setup/. Nothing else. Idempotent.
#
# What it does NOT do: install Claude Code, OAuth/auth, or any MCP servers.
# Those go through Anthropic's official install paths. This is just the
# recommendation set; your Claude agent applies it during /setup.

set -euo pipefail

REPO_URL="${CLAUDE_PERSONAL_STARTER_REPO:-https://github.com/Tugboat-Solutions-Inc/claude-personal-starter.git}"
REPO_DIR="${CLAUDE_PERSONAL_STARTER_DIR:-$HOME/.claude-personal-starter}"
SKILL_DIR="$HOME/.claude/skills/setup"

red()   { printf "\033[31m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
blue()  { printf "\033[34m%s\033[0m\n" "$*"; }

require() {
  command -v "$1" >/dev/null 2>&1 || { red "$1 not found in PATH. Install it first."; exit 1; }
}

main() {
  blue "claude-personal-starter bootstrap"

  require git
  if ! command -v claude >/dev/null 2>&1; then
    red "claude not found in PATH."
    echo "Install Claude Code first via the official path:"
    echo "  curl -fsSL https://claude.ai/install.sh | sh"
    echo "Then run 'claude' once to OAuth-login (press Enter on the success page,"
    echo "type /exit to quit), then re-run this bootstrap."
    exit 1
  fi

  if [ -d "$REPO_DIR/.git" ]; then
    blue "Updating $REPO_DIR ..."
    git -C "$REPO_DIR" fetch --quiet origin
    git -C "$REPO_DIR" reset --hard --quiet origin/main
  else
    blue "Cloning to $REPO_DIR ..."
    git clone --quiet "$REPO_URL" "$REPO_DIR"
  fi

  mkdir -p "$SKILL_DIR"
  cp "$REPO_DIR/skills/setup/SKILL.md" "$SKILL_DIR/SKILL.md"

  green "Installed."
  echo ""
  echo "Next:"
  echo "  1. Run: claude"
  echo "  2. In the prompt, type: /setup"
  echo "  3. Pick the components you want."
  echo ""
  echo "The /setup skill will walk you through everything else — including which"
  echo "MCP authenticate commands to run for things like Gmail and Calendar."
}

main "$@"
