#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

JHP_REPO="/workspaces/Job_Hunter_Platform/job-hunter-pro"
DOCS="/downloads"

echo "=== UBUNTU: VERIFY BINDS ==="
[ -d "$JHP_REPO" ] || { echo "FAIL: repo bind missing: $JHP_REPO"; exit 1; }
[ -f "$JHP_REPO/app.py" ] || { echo "FAIL: app.py missing in Ubuntu repo"; exit 1; }
[ -d "$DOCS" ] || { echo "FAIL: downloads bind missing: $DOCS"; exit 1; }

echo
echo "=== UBUNTU: SYSTEM TOOLS ==="
apt-get update -y
apt-get install -y curl ca-certificates git jq ripgrep tree \
  python3 python3-venv python3-pip build-essential

echo
echo "=== UBUNTU: NODE 20+ ==="
need_node=0
if ! command -v node >/dev/null 2>&1; then
  need_node=1
else
  major="$(node -e 'process.stdout.write(String(parseInt(process.versions.node)))' 2>/dev/null || echo 0)"
  [ "$major" -ge 18 ] || need_node=1
fi

if [ "$need_node" -eq 1 ]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

echo "node: $(node -v)"
echo "npm : $(npm -v)"

echo
echo "=== UBUNTU: CLAUDE CODE CLI ==="
npm config delete ignore-scripts || true
npm config set include optional
npm uninstall -g @anthropic-ai/claude-code 2>/dev/null || true
npm install -g @anthropic-ai/claude-code@latest --include=optional --foreground-scripts

if claude --version; then
  echo "Claude Code OK."
else
  echo "WARN: Claude CLI still not available after npm install."
  echo "The repo scaffold will still be built."
fi

cd "$JHP_REPO"

echo
echo "=== UBUNTU: PYTHON VENV + DEPENDENCIES ==="
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip wheel

if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  pip install flask gunicorn requests google-auth google-cloud-firestore google-cloud-storage pydantic
fi

echo
echo "=== UBUNTU: BUILD FULL CLAUDE PROJECT SCAFFOLD ==="
JHP_REPO="$JHP_REPO" DOCS="$DOCS" python3 .claude_setup/JHP_SCAFFOLD_FINAL.py

echo
echo "=== UBUNTU: SAFE LOCAL PROOF, ZERO LIVE PROVIDER SPEND ==="
bash .claude/scripts/safe_local_proof.sh

echo
echo "=== UBUNTU: SETUP SUMMARY ==="
pwd
echo "Agents  : $(find .claude/agents -maxdepth 1 -type f | wc -l)"
echo "Skills  : $(find .claude/skills -name SKILL.md | wc -l)"
echo "Commands: $(find .claude/commands -maxdepth 1 -type f | wc -l)"
echo "Scripts : $(find .claude/scripts -maxdepth 1 -type f | wc -l)"
echo
git status --short

echo
echo "================================================================"
echo "SETUP COMPLETE"
echo
echo "Later re-enter with:"
echo 'proot-distro login ubuntu --bind "$HOME/Workspaces:/workspaces" --bind "$HOME/storage/downloads:/downloads"'
echo "cd $JHP_REPO"
echo ". .venv/bin/activate"
echo "claude"
echo
echo "Inside Claude, run:"
echo "/fix-live-jobs"
echo "================================================================"

if command -v claude >/dev/null 2>&1; then
  echo
  echo "=== OPENING CLAUDE CODE ==="
  echo "When Claude opens, type: /fix-live-jobs"
  claude
fi
