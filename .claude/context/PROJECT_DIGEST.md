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
