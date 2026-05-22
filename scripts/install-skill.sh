#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${MODAL_PARALLEL_SEARCH_REPO_URL:-https://github.com/krittaprot/modal-parallel-search.git}"
SKILLS_HOME="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"
REPO_DIR="$SKILLS_HOME/.repos/modal-parallel-search"
SKILL_DIR="$SKILLS_HOME/modal-parallel-search"

mkdir -p "$SKILLS_HOME/.repos"

if [ -d "$REPO_DIR/.git" ]; then
  echo "Updating repo at $REPO_DIR"
  git -C "$REPO_DIR" pull --ff-only
else
  echo "Cloning repo to $REPO_DIR"
  rm -rf "$REPO_DIR"
  git clone "$REPO_URL" "$REPO_DIR"
fi

if [ -L "$SKILL_DIR" ] || [ -e "$SKILL_DIR" ]; then
  rm -rf "$SKILL_DIR"
fi

ln -s "$REPO_DIR/skills/modal-parallel-search" "$SKILL_DIR"

echo ""
echo "Installed Modal Parallel Search skill:"
echo "  $SKILL_DIR"
echo ""
echo "Expected skill file:"
echo "  $SKILL_DIR/SKILL.md"
echo ""
echo "Next steps:"
echo "  uv tool install modal"
echo "  modal setup"
echo "  modal run $SKILL_DIR/scripts/modal_search_cli.py --query \"Modal Python serverless\" --max-results 1"
