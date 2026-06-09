# Claude Code Project Instructions - Job Hunter Pro

You are a senior software engineer working on Job Hunter Pro, a Flask app deployed to Google Cloud Run for Michael Ware.

Before editing anything, read all six project documents:

@context/AI_JOB_AGENT_1.txt
@context/AI_JOB_AGENT_2.txt
@context/AI_JOB_AGENT_3.txt
@context/AI_JOB_AGENT_4.txt
@context/AI_JOB_AGENT_5.txt
@context/AI_JOB_AGENT_6.txt

Non-negotiable rules:

- Never print, hardcode, commit, or expose secrets.
- All provider keys live in Secret Manager only.
- Never put a token in a Scheduler URL.
- /api/ingest must be protected by Cloud Scheduler OIDC.
- Do not call /api/ingest unless explicitly instructed.
- Do not call live /api/jobs unless explicitly instructed.
- Do not deploy until local inspection, compile proof, safe endpoint proof, and diff review pass.
- OpenAI, Gemini, Claude, Groq, and xAI are enrichment/classification providers only.
- They are not job discovery sources.
- Discovery sources are SerpAPI Jobs, SerpAPI Organic, Adzuna, USAJobs, Jooble, Careerjet, The Muse, and Google Places/opportunities.

Current repair target:

Fix live jobs.

Real provider results must be visible even when address, radius, or transit resolution is incomplete.
Missing address/radius/transit must become resolution_flags, not hard rejection.
All available SEARCH providers must be attempted fairly before one provider fills the cap.
The UI must show accepted jobs plus unresolved live candidates.
Provider breakdown and source evidence must be preserved.
Page boot must not run paid live discovery automatically.

Required proof before deploy:

1. python3 -m py_compile $(git ls-files "*.py")
2. bash .claude/scripts/safe_local_proof.sh
3. git diff --check
4. git diff --stat

Then stop and show the diff.
