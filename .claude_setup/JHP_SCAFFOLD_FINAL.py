from pathlib import Path
import os
import shutil
import textwrap
import time

repo = Path(os.environ["JHP_REPO"])
downloads = Path(os.environ.get("DOCS", "/downloads"))

if not repo.exists():
    raise SystemExit(f"FAIL: repo missing: {repo}")
if not (repo / "app.py").exists():
    raise SystemExit(f"FAIL: app.py missing: {repo}")

def write(rel, body, mode=None):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")
    if mode is not None:
        path.chmod(mode)

existing = repo / ".claude"
if existing.exists():
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup = repo / f".claude_backup_{ts}"
    shutil.copytree(existing, backup)
    print(f"backup created: {backup.name}")

dirs = [
    ".claude/context",
    ".claude/agents",
    ".claude/commands",
    ".claude/skills/jhp-live-jobs",
    ".claude/skills/jhp-safe-proof",
    ".claude/skills/jhp-security-scan",
    ".claude/skills/jhp-git-commit-push",
    ".claude/skills/jhp-deploy-proof",
    ".claude/skills/jhp-context-compact",
    ".claude/skills/jhp-route-audit",
    ".claude/skills/jhp-ui-truth",
    ".claude/skills/jhp-provider-fanout",
    ".claude/scripts",
    ".claude/hooks",
    ".claude/workflows",
    ".claude/checklists",
    ".claude/tasks",
    ".claude/backups",
    ".claude/logs",
]
for d in dirs:
    (repo / d).mkdir(parents=True, exist_ok=True)

doc_candidates = [
    (["docs/AI_JOB_AGENT_1.txt", downloads / "AI JOB AGENT (1).txt"], "AI_JOB_AGENT_1.txt"),
    (["docs/AI_JOB_AGENT_2.txt", downloads / "AI JOB AGENT (2).txt"], "AI_JOB_AGENT_2.txt"),
    (["docs/AI_JOB_AGENT_3.txt", downloads / "AI JOB AGENT (3).txt"], "AI_JOB_AGENT_3.txt"),
    (["docs/AI_JOB_AGENT_4.txt", downloads / "AI JOB AGENT (4).txt"], "AI_JOB_AGENT_4.txt"),
    (["docs/AI_JOB_AGENT_5_UIUX_Handoff.md", downloads / "AI JOB AGENT (5) (1).txt"], "AI_JOB_AGENT_5.md"),
    (["docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md", downloads / "AI JOB AGENT (6).txt"], "AI_JOB_AGENT_6.md"),
]

for candidates, dest in doc_candidates:
    found = None
    for item in candidates:
        p = repo / item if isinstance(item, str) else item
        if p.exists():
            found = p
            break
    if not found:
        raise SystemExit(f"FAIL: missing required document for {dest}")
    shutil.copy2(found, repo / ".claude/context" / dest)
    print(f"doc copied: {found} -> .claude/context/{dest}")

write("CLAUDE.md", """
# Job Hunter Pro

Load the complete Claude Code project operating system:

@.claude/CLAUDE.md
""")

write(".claude/context/PROJECT_DIGEST.md", """
# Job Hunter Pro Durable Digest

Use this digest after the six documents have been read once. Do not waste context by rereading every document repeatedly unless the digest is insufficient.

## Identity

Project: Job Hunter Pro
Owner: Michael Ware
Cloud Run service: job-hunter-pro
GCP project: ai-job-agent-498702
Region: us-central1
Termux repo: ~/Workspaces/Job_Hunter_Platform/job-hunter-pro
Ubuntu repo: /workspaces/Job_Hunter_Platform/job-hunter-pro

## Architecture

Trust current code over stale notes. Inspect first.

Likely active files:
- app.py
- api/index.py
- api/__init__.py
- api/ingest.py
- search/federated.py
- search/budget.py
- search/usage_tracker.py
- pipeline/reject.py
- pipeline/normalize.py
- pipeline/run.py
- providers/search/*.py
- providers/reasoning/*.py
- web/templates/index.html
- web/static/js/*.js

## Hard rules

No hardcoded secrets.
No printed secrets.
No Scheduler URL tokens.
No /api/ingest unless explicitly instructed.
No live /api/jobs without dry_run unless explicitly instructed.
No deploy unless explicitly instructed.
Compile before deploy.
Run safe local proof before deploy.
After deploy, check /api/health.
If health fails, check logs.

## Provider law

OpenAI, Gemini, Claude, Groq, and xAI are enrichment/classification only.
They are not job discovery sources.

Discovery sources:
SerpAPI Jobs, SerpAPI Organic, Adzuna, USAJobs, Jooble, Careerjet, The Muse, Google Places/opportunities.

## Live jobs defect

Real provider jobs must not disappear because address/radius/transit resolution failed.
Missing resolution becomes resolution_flags / needs_resolution, not deletion.
All available search providers must get a fair turn before one fills the cap.
The UI must show accepted candidates plus unresolved candidates.
Provider breakdown and source URLs must be preserved.
""")

write(".claude/CLAUDE.md", """
# Claude Code Operating System — Job Hunter Pro

You are a senior software engineer building Job Hunter Pro for Michael Ware.

## Source documents

Read these at the beginning of a major task, then use PROJECT_DIGEST, skills, agents, scripts, and checklists to avoid wasting context.

@context/AI_JOB_AGENT_1.txt
@context/AI_JOB_AGENT_2.txt
@context/AI_JOB_AGENT_3.txt
@context/AI_JOB_AGENT_4.txt
@context/AI_JOB_AGENT_5.md
@context/AI_JOB_AGENT_6.md

## Durable context

@context/PROJECT_DIGEST.md

## Absolute rules

- Never print, hardcode, commit, or expose secrets.
- Provider keys live in Secret Manager only.
- Never put tokens in Scheduler URLs.
- /api/ingest must be protected by Cloud Scheduler OIDC.
- Do not call /api/ingest unless Michael explicitly says to.
- Do not call live /api/jobs unless Michael explicitly says to.
- Do not deploy unless Michael explicitly says deploy.
- LLMs are enrichment/classification only.
- Discovery sources are SerpAPI Jobs, SerpAPI Organic, Adzuna, USAJobs, Jooble, Careerjet, The Muse, and Google Places/opportunities.
- Inspect current code before patching.
- Do not patch large files blindly with regex.
- Compile before deploy.
- Run safe local proof before deploy.
- After deploy, check /api/health.
- If health fails, check logs.
- Do not fake telemetry, jobs, provider counts, logs, or success.

## Model and context workflow

Use strongest available model for planning, architecture, security, and final review.
Use implementation agents for edits.
Use cheap agents only for summaries, inventories, and repetitive scanning.
At 75 percent context, stop and compact durable state into .claude/context/SESSION_STATE.md before continuing.
Do not reread all six documents repeatedly.

## Current priority

Fix live jobs visibility and fair provider fanout.

Real provider results must be visible even when address/radius/transit resolution is incomplete.
Missing resolution must become resolution_flags, not hard rejection.
All available SEARCH providers must be attempted fairly before one provider fills the cap.
The UI must show accepted jobs plus unresolved candidates.
Provider breakdown, source URLs, raw counts, errors, and resolution evidence must be preserved.
Page boot must not run paid live discovery automatically.

## Mandatory proof

Run:

bash .claude/scripts/safe_local_proof.sh
git diff --check
git diff --stat

Then stop and show the diff.
""")

write(".claude/context/SESSION_STATE.md", """
# Session State

Current task: fix live jobs visibility and provider fanout.

Rules:
- Do not deploy unless explicitly told.
- Do not call live /api/jobs unless explicitly told.
- Do not call /api/ingest unless explicitly told.
- Do not print secrets.

Update this file when context approaches 75 percent.
""")

write(".claude/settings.json", """
{
  "permissions": {
    "allow": [
      "Bash(pwd)",
      "Bash(ls *)",
      "Bash(find *)",
      "Bash(grep *)",
      "Bash(rg *)",
      "Bash(cat *)",
      "Bash(sed -n *)",
      "Bash(git status *)",
      "Bash(git diff *)",
      "Bash(git diff --check)",
      "Bash(git diff --stat)",
      "Bash(git ls-files *)",
      "Bash(python3 -m py_compile *)",
      "Bash(python3 .claude/scripts/proof_runner.py)",
      "Bash(bash .claude/scripts/inspect_stack.sh)",
      "Bash(bash .claude/scripts/safe_local_proof.sh)",
      "Bash(bash .claude/scripts/predeploy_proof.sh)",
      "Bash(bash .claude/scripts/make_backup.sh)",
      "Bash(bash .claude/scripts/update_session_state.sh)",
      "Bash(bash .claude/scripts/export_context_bundle.sh)"
    ],
    "ask": [
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git push *)",
      "Bash(gcloud run deploy *)",
      "Bash(curl *)"
    ],
    "deny": [
      "Bash(git push --force*)",
      "Bash(* /api/ingest*)",
      "Bash(*api/ingest*)",
      "Bash(*SERPAPI_KEY*)",
      "Bash(*OPENAI_API_KEY*)",
      "Bash(*ANTHROPIC_API_KEY*)",
      "Bash(*GEMINI_API_KEY*)",
      "Bash(*GROQ_API_KEY*)",
      "Bash(*XAI_API_KEY*)"
    ]
  },
  "statusLine": {
    "type": "command",
    "command": ".claude/scripts/statusline.sh",
    "refreshInterval": 5,
    "padding": 1
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/guard_bash.sh"
          }
        ]
      }
    ]
  }
}
""")

write(".claude/scripts/statusline.sh", """
#!/usr/bin/env bash
input="$(cat)"
if command -v jq >/dev/null 2>&1; then
  MODEL="$(printf '%s' "$input" | jq -r '.model.display_name // .model.name // "model?"' 2>/dev/null || echo model?)"
  PCT="$(printf '%s' "$input" | jq -r '.context_window.used_percentage // 0' 2>/dev/null | cut -d. -f1)"
  DIR="$(printf '%s' "$input" | jq -r '.workspace.current_dir // ""' 2>/dev/null)"
else
  MODEL="model?"
  PCT="0"
  DIR="$(pwd)"
fi
BRANCH="$(git branch --show-current 2>/dev/null || true)"
WARN=""
[ "${PCT:-0}" -ge 75 ] 2>/dev/null && WARN=" | COMPACT NOW"
echo "[$MODEL] ${DIR##*/} ${BRANCH:+| $BRANCH} | ${PCT}% context${WARN}"
""", 0o755)

write(".claude/hooks/guard_bash.sh", """
#!/usr/bin/env bash
payload="$(cat)"
cmd="$(printf '%s' "$payload" | python3 -c '
import sys, json
try:
    d=json.load(sys.stdin)
    ti=d.get("tool_input") or {}
    print(ti.get("command") or ti.get("bash_command") or "")
except Exception:
    pass
' 2>/dev/null || true)"

case "$cmd" in
  *"/api/ingest"*|*"api/ingest"*)
    echo "BLOCKED: /api/ingest is protected." >&2
    exit 2 ;;
  *"SERPAPI_KEY"*|*"OPENAI_API_KEY"*|*"ANTHROPIC_API_KEY"*|*"GEMINI_API_KEY"*|*"GROQ_API_KEY"*|*"XAI_API_KEY"*)
    echo "BLOCKED: command appears to expose secret env vars." >&2
    exit 2 ;;
  *"git push --force"*|*"push --force"*)
    echo "BLOCKED: force push forbidden." >&2
    exit 2 ;;
esac
exit 0
""", 0o755)

agents = {
"opus-architect.md": ("opus", "Architecture/root-cause planning. Inspect first. Do not patch blindly."),
"opus-security-auditor.md": ("opus", "Secrets/OIDC/Scheduler/security review. Never print secrets."),
"opus-final-reviewer.md": ("opus", "Final high-risk diff review before commit/deploy."),
"sonnet-backend-engineer.md": ("sonnet", "Backend implementation for Flask/API/routes."),
"sonnet-provider-fanout-engineer.md": ("sonnet", "Provider fanout, caps, provider_breakdown, raw job normalization."),
"sonnet-job-visibility-engineer.md": ("sonnet", "Convert hard rejection into resolution_flags and visible unresolved jobs."),
"sonnet-frontend-truth-engineer.md": ("sonnet", "Render accepted and unresolved jobs truthfully."),
"sonnet-data-contract-auditor.md": ("sonnet", "Verify backend JSON matches frontend expectations."),
"sonnet-testing-engineer.md": ("sonnet", "Compile and safe local proof only."),
"sonnet-observability-engineer.md": ("sonnet", "Health/debug/provider breakdown/truth telemetry."),
"sonnet-dependency-engineer.md": ("sonnet", "Python/JS deps and Termux/Ubuntu compatibility."),
"sonnet-cloud-run-engineer.md": ("sonnet", "Cloud Run deploy plan, health, logs. No deploy without approval."),
"sonnet-scheduler-oidc-engineer.md": ("sonnet", "Cloud Scheduler OIDC and /api/ingest protection."),
"sonnet-quota-budget-auditor.md": ("sonnet", "Prevent hidden SerpAPI/provider quota burn."),
"sonnet-route-surface-auditor.md": ("sonnet", "Route map, blueprint shadowing, active endpoint surface."),
"sonnet-storage-engineer.md": ("sonnet", "Firestore/GCS store contracts, no secrets."),
"sonnet-uiux-engineer.md": ("sonnet", "Mobile UI, card layout, truth-preserving UX."),
"sonnet-refactor-surgeon.md": ("sonnet", "Clean small refactors after proof; no blind regex patching."),
"haiku-file-indexer.md": ("haiku", "Cheap file inventory and grep summaries."),
"haiku-diff-summarizer.md": ("haiku", "Cheap diff and checklist summaries."),
"haiku-log-summarizer.md": ("haiku", "Cheap log summary without secrets."),
"git-release-manager.md": ("sonnet", "Git add/commit/push only after proof and explicit approval.")
}

for filename, (model, desc) in agents.items():
    name = filename[:-3]
    write(f".claude/agents/{filename}", f"""
---
name: {name}
description: {desc}
model: {model}
tools: Read, Grep, Glob, Bash, Edit
---

You are {name} for Job Hunter Pro.

Follow .claude/CLAUDE.md.
Use .claude/context/PROJECT_DIGEST.md before rereading full documents.
Do not print secrets.
Do not call live /api/jobs unless explicitly instructed.
Do not call /api/ingest unless explicitly instructed.
Do not deploy unless explicitly instructed.
Run safe proof before recommending commit/deploy.
""")

skills = {
"jhp-live-jobs": "Fix live jobs provider fanout and visibility without spending live provider quota.",
"jhp-safe-proof": "Run mandatory local proof without external live discovery quota.",
"jhp-security-scan": "Scan for secret leaks, unsafe ingest auth, URL tokens, and hidden quota burns.",
"jhp-git-commit-push": "Stage, commit, and push only after proof and explicit approval.",
"jhp-deploy-proof": "Predeploy proof and Cloud Run health/log plan.",
"jhp-context-compact": "Compact durable state at 75 percent context without rereading everything.",
"jhp-route-audit": "Audit Flask routes, blueprint shadowing, and mounted backend surface.",
"jhp-ui-truth": "Keep UI truthful: no fake telemetry/jobs/provider counts.",
"jhp-provider-fanout": "Ensure all search providers get fair turn before one fills cap."
}

for skill, desc in skills.items():
    write(f".claude/skills/{skill}/SKILL.md", f"""
---
name: {skill}
description: {desc}
allowed-tools: Bash(git status *) Bash(git diff *) Bash(rg *) Bash(python3 -m py_compile *) Bash(bash .claude/scripts/safe_local_proof.sh)
---

# {skill}

Use project rules from .claude/CLAUDE.md.

Never print secrets.
Never call /api/ingest unless explicitly instructed.
Never call live /api/jobs unless explicitly instructed.
Never deploy unless explicitly instructed.

For live jobs:
- Missing address/radius/transit becomes resolution_flags, not deletion.
- All available search providers get fair fanout.
- LLMs are enrichment/classification only.
- UI shows accepted plus unresolved candidates.
- Provider breakdown and source URLs are preserved.
""")

write(".claude/scripts/inspect_stack.sh", """
#!/usr/bin/env bash
set -euo pipefail
pwd
git status --short
echo "=== key files ==="
ls -la app.py api/index.py api/__init__.py api/ingest.py \
  search/federated.py search/budget.py search/usage_tracker.py \
  pipeline/reject.py pipeline/normalize.py pipeline/run.py \
  web/templates/index.html 2>/dev/null || true
echo "=== key patterns ==="
rg -n "MAX_RADIUS_MILES|MAX_TRANSIT_SECONDS|FOOD_TERMS|resolution_flags|needs_resolution|provider_breakdown|dry_run|_surface|placeholder_blueprint|def fetch_all|def run_pipeline|def reject|def normalize" \
  app.py api search pipeline providers web/static/js web/templates 2>/dev/null || true
""", 0o755)

write(".claude/scripts/proof_runner.py", """
import sys
import json

try:
    from app import app
except Exception as e:
    print(f"FAIL: could not import app: {e}")
    sys.exit(1)

c = app.test_client()

def get(path, expect=200):
    r = c.get(path)
    label = "OK" if r.status_code == expect else "FAIL"
    print(f"[{label}] GET {path} -> {r.status_code}")
    if r.status_code != expect:
        sys.exit(1)
    return r

get("/")
get("/api/providers")
get("/api/health")

dry = get("/api/jobs?dry_run=1").get_json()
if not dry or dry.get("dry_run") is not True:
    print("FAIL: /api/jobs?dry_run=1 did not return dry_run=true")
    print(json.dumps(dry, indent=2)[:500])
    sys.exit(1)
print("[OK] dry_run=true confirmed")

surface = c.get("/api/_surface")
if surface.status_code == 200:
    data = surface.get_json() or {}
    if data.get("placeholder_blueprint_registered") is True:
        print("FAIL: placeholder blueprint shadow detected")
        sys.exit(1)
    print(f"[OK] _surface placeholder_blueprint_registered={data.get('placeholder_blueprint_registered')}")
else:
    print(f"WARN: /api/_surface unavailable -> {surface.status_code}")

print("PASS safe local proof")
""")

write(".claude/scripts/safe_local_proof.sh", """
#!/usr/bin/env bash
set -euo pipefail
if [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
fi
echo "--- compile check ---"
python3 -m py_compile $(git ls-files "*.py")
echo "--- safe flask proof ---"
python3 .claude/scripts/proof_runner.py
echo "--- diff checks ---"
git diff --check
git diff --stat
""", 0o755)

write(".claude/scripts/predeploy_proof.sh", """
#!/usr/bin/env bash
set -euo pipefail
bash .claude/scripts/inspect_stack.sh
bash .claude/scripts/safe_local_proof.sh
echo "PASS predeploy proof. Deploy only after explicit approval."
""", 0o755)

write(".claude/scripts/cloud_run_health.sh", """
#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="${PROJECT_ID:-ai-job-agent-498702}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-job-hunter-pro}"
URL="$(gcloud run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
echo "SERVICE_URL=$URL"
curl -fsS "$URL/api/health"
echo
""", 0o755)

write(".claude/scripts/logs_on_fail.sh", """
#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="${PROJECT_ID:-ai-job-agent-498702}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-job-hunter-pro}"
gcloud run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" --format="table(metadata.name,status.url,status.latestReadyRevisionName,status.conditions[0].type,status.conditions[0].status)"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE" --project "$PROJECT_ID" --limit 80 --format="value(timestamp,severity,textPayload,jsonPayload.message)"
""", 0o755)

write(".claude/scripts/make_backup.sh", """
#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d_%H%M%S)"
OUT=".claude/backups/job_hunter_backup_${TS}.tar.gz"
tar --exclude=.git --exclude=.venv --exclude=__pycache__ --exclude=.claude/backups -czf "$OUT" .
echo "$OUT"
""", 0o755)

write(".claude/scripts/jhp_commit.sh", """
#!/usr/bin/env bash
set -euo pipefail
MSG="${1:-}"
[ -n "$MSG" ] || { echo "usage: bash .claude/scripts/jhp_commit.sh 'message'"; exit 1; }
bash .claude/scripts/safe_local_proof.sh
git add app.py api search providers pipeline web .claude CLAUDE.md docs scripts 2>/dev/null || true
git status --short
git commit -m "$MSG"
""", 0o755)

write(".claude/scripts/jhp_push.sh", """
#!/usr/bin/env bash
set -euo pipefail
git status --short
git push origin HEAD
""", 0o755)

write(".claude/scripts/update_session_state.sh", """
#!/usr/bin/env bash
set -euo pipefail
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
{
  echo "# Session State"
  echo
  echo "Updated: $TS"
  echo
  echo "## Git status"
  echo
  git status --short || true
  echo
  echo "## Diff stat"
  echo
  git diff --stat || true
  echo
  echo "## Current instructions"
  echo
  echo "- Do not deploy unless explicitly instructed."
  echo "- Do not call live /api/jobs unless explicitly instructed."
  echo "- Do not call /api/ingest unless explicitly instructed."
  echo "- Do not print secrets."
} > .claude/context/SESSION_STATE.md
cat .claude/context/SESSION_STATE.md
""", 0o755)

write(".claude/scripts/export_context_bundle.sh", """
#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d_%H%M%S)"
OUT="$HOME/storage/downloads/JHP_CLAUDE_CONTEXT_${TS}.tar.gz"
tar -czf "$OUT" .claude CLAUDE.md
echo "$OUT"
""", 0o755)

commands = {
"fix-live-jobs.md": """
# /fix-live-jobs

Do not deploy.
Do not call live /api/jobs.
Do not call /api/ingest.
Do not print secrets.

Use these agents in order:
1. opus-architect
2. haiku-file-indexer
3. sonnet-route-surface-auditor
4. sonnet-provider-fanout-engineer
5. sonnet-job-visibility-engineer
6. sonnet-frontend-truth-engineer
7. sonnet-data-contract-auditor
8. sonnet-testing-engineer
9. opus-security-auditor
10. opus-final-reviewer

Inspect current code first. Trust current repo over stale docs.

Focus:
- search/federated.py provider fairness
- pipeline/reject.py hard rejection gates
- pipeline/normalize.py resolution flags
- api/index.py jobs assembler / dry_run / payload
- web/static/js and web/templates UI display

Proof:
bash .claude/scripts/safe_local_proof.sh

Stop after proof and show diff.
""",
"audit-stack.md": """
# /audit-stack

Run:
bash .claude/scripts/inspect_stack.sh

Do not edit unless asked.
""",
"safe-proof.md": """
# /safe-proof

Run:
bash .claude/scripts/safe_local_proof.sh
""",
"predeploy-proof.md": """
# /predeploy-proof

Run:
bash .claude/scripts/predeploy_proof.sh

Do not deploy.
""",
"review-diff.md": """
# /review-diff

Run:
git diff --check
git diff --stat
git diff

Use opus-final-reviewer and code-reviewer.
Do not deploy.
""",
"security-scan.md": """
# /security-scan

Use opus-security-auditor, sonnet-scheduler-oidc-engineer, and sonnet-quota-budget-auditor.
Do not print secret values.
""",
"commit-proof.md": """
# /commit-proof

Only after explicit commit approval.

Run:
bash .claude/scripts/jhp_commit.sh "$ARGUMENTS"
""",
"push-proof.md": """
# /push-proof

Only after explicit push approval.

Run:
bash .claude/scripts/jhp_push.sh
""",
"deploy-only-if-approved.md": """
# /deploy-only-if-approved

Only after Michael explicitly says deploy.

Before deploy:
bash .claude/scripts/predeploy_proof.sh

After deploy:
bash .claude/scripts/cloud_run_health.sh

If health fails:
bash .claude/scripts/logs_on_fail.sh
""",
"compact-state.md": """
# /compact-state

Run:
bash .claude/scripts/update_session_state.sh

Then continue using .claude/context/SESSION_STATE.md and PROJECT_DIGEST.md.
"""
}

for name, body in commands.items():
    write(f".claude/commands/{name}", body)

write(".claude/workflows/PERFECT_CODE_WORKFLOW.md", """
# Perfect Code Workflow

S0 Confirm repo path.
S1 Read docs/digest once.
S2 Inspect current active files.
S3 Identify exact defect.
S4 Backup.
S5 Patch only proven defect.
S6 Compile.
S7 Safe local proof.
S8 Diff check.
S9 Security/quota review.
S10 Commit only after approval.
S11 Push only after approval.
S12 Deploy only after approval, then health, then logs if fail.
""")

write(".claude/checklists/LIVE_JOBS_FIX_CHECKLIST.md", """
# Live Jobs Fix Checklist

- Search providers only for discovery.
- LLMs enrichment/classification only.
- All available search providers get a fair turn.
- One provider cannot consume cap before others run.
- Missing address is a flag, not deletion.
- Missing radius is a flag, not deletion.
- Missing transit is a flag, not deletion.
- UI shows accepted and unresolved jobs.
- Provider breakdown visible.
- Source URL preserved.
- Dry run is safe.
- Page boot does not call live discovery.
- /api/ingest remains protected.
""")

write(".claude/tasks/fix_live_jobs_prompt.txt", """
Run /fix-live-jobs.

Use installed agents, skills, scripts, settings, hooks, and workflow.
Do not deploy.
Do not call live /api/jobs.
Do not call /api/ingest.
Do not print secrets.
Do not fake data.
""")

print()
print("=== JHP FULL SCAFFOLD COMPLETE ===")
print(f"repo     : {repo}")
print(f"agents   : {len(list((repo / '.claude/agents').glob('*.md')))}")
print(f"skills   : {len(list((repo / '.claude/skills').glob('*/SKILL.md')))}")
print(f"commands : {len(list((repo / '.claude/commands').glob('*.md')))}")
print(f"scripts  : {len(list((repo / '.claude/scripts').glob('*')))}")
