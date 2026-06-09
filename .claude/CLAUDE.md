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
