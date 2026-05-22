#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${MODAL_PARALLEL_SEARCH_REPO_URL:-https://github.com/krittaprot/modal-parallel-search.git}"
SKILLS_HOME="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"
REPO_DIR="$SKILLS_HOME/.repos/modal-parallel-search"
SKILL_DIR="$SKILLS_HOME/modal-parallel-search"

info() { printf '\033[1;34m%s\033[0m\n' "$*"; }
success() { printf '\033[1;32m%s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m%s\033[0m\n' "$*"; }
die() { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

info "Installing Modal Parallel Search agent skill"

have git || die "git is required. Install Git, then run this script again."
have ln || die "ln is required to create the skill symlink."

mkdir -p "$SKILLS_HOME/.repos"

if [ -d "$REPO_DIR/.git" ]; then
  info "Updating existing repo: $REPO_DIR"
  git -C "$REPO_DIR" pull --ff-only
else
  info "Cloning repo: $REPO_URL"
  rm -rf "$REPO_DIR"
  git clone "$REPO_URL" "$REPO_DIR"
fi

if [ ! -f "$REPO_DIR/SKILL.md" ]; then
  die "SKILL.md was not found at $REPO_DIR/SKILL.md. The checkout may be incomplete."
fi

if [ -L "$SKILL_DIR" ]; then
  CURRENT_TARGET="$(readlink "$SKILL_DIR" || true)"
  if [ "$CURRENT_TARGET" != "$REPO_DIR" ]; then
    warn "Replacing existing symlink: $SKILL_DIR -> $CURRENT_TARGET"
  fi
  rm -f "$SKILL_DIR"
elif [ -e "$SKILL_DIR" ]; then
  BACKUP_DIR="$SKILL_DIR.backup.$(date +%Y%m%d-%H%M%S)"
  warn "A non-symlink already exists at $SKILL_DIR"
  warn "Moving it to $BACKUP_DIR instead of deleting it."
  mv "$SKILL_DIR" "$BACKUP_DIR"
fi

ln -s "$REPO_DIR" "$SKILL_DIR"

success "Installed skill at: $SKILL_DIR"
printf '\n'
printf 'Expected files:\n'
printf '  %s/SKILL.md\n' "$SKILL_DIR"
printf '  %s/scripts/modal_search_cli.py\n' "$SKILL_DIR"
printf '\n'

if have modal; then
  success "Modal CLI found: $(modal --version 2>/dev/null || printf 'installed')"
  printf '\n'
  printf 'Next: verify your Modal login and run a tiny search:\n'
  printf '  modal token info\n'
  printf '  modal run %s/scripts/modal_search_cli.py --query "Modal Python serverless" --max-results 1\n' "$SKILL_DIR"
else
  warn "Modal CLI was not found yet."
  printf '\n'
  printf 'Next steps:\n'
  printf '  uv tool install modal\n'
  printf '  modal setup\n'
  printf '  modal run %s/scripts/modal_search_cli.py --query "Modal Python serverless" --max-results 1\n' "$SKILL_DIR"
  printf '\n'
  printf 'No uv? Use:\n'
  printf '  python3 -m pip install --user modal\n'
fi

printf '\n'
printf 'Tip for agents: read %s/SKILL.md, then run the modal_search_cli.py command above.\n' "$SKILL_DIR"
