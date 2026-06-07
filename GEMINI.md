# GEMINI.md — Job Hunter Pro Operating Instructions

You are working on Job Hunter Pro, a Flask app deployed on Google Cloud Run for Michael Ware.

Before making any recommendation or code change, read every byte of these project documents:

- docs/AI_JOB_AGENT_1.txt
- docs/AI_JOB_AGENT_2.txt
- docs/AI_JOB_AGENT_3.txt
- docs/AI_JOB_AGENT_4.txt

If any of those four files are missing, stop and report that the project documents are incomplete.

## Non-negotiable rules

1. Never hardcode, print, echo, log, or expose secrets.
2. All keys and credentials live in Google Secret Manager only.
3. Never guess or patch blindly.
4. Always inspect the current code before modifying it.
5. Always compile locally with python -m py_compile before deploy.
6. Only after compile succeeds, deploy.
7. After deploy, check /api/health.
8. If health fails, check Cloud Run logs.
9. Never claim LLM APIs search for jobs.
10. OpenAI, Gemini, Claude, Groq, and xAI are enrichment/classification only.
11. Discovery sources are SerpAPI, Adzuna, USAJobs, Jooble, Careerjet, and The Muse.
12. Never burn SerpAPI on page load.
13. Default UI calls must be usage, opportunities, history, and dry-run only.
14. Never put a token in a Scheduler URL.
15. /api/ingest is protected by Cloud Scheduler OIDC only.
16. Never patch a large file with regex blindly.
17. If a patch stack is corrupted, write a clean file and overwrite.
18. Development environment is Android ARM64 Termux.
19. Keep all terminal commands copy-paste safe for Termux.
20. Follow stages S0 through S12 from the project documents.
21. Do not skip stages.
22. Do not deploy until S12.

## Ownership boundaries

Engine/backend/system code may be built in a boring, standard, deterministic way.

Michael keeps creative control over:

- UI/UX
- frontend layouts
- colors
- spacing
- cards
- filters
- animations
- dashboard feel
- visual copy
- final user-facing design

For S10 web/frontend work, create only semantic hooks, safe placeholders, and clean module boundaries unless Michael explicitly approves the visual direction.

## Required workflow

For every stage:

1. Inspect files.
2. State what exists.
3. State what is missing.
4. Make the smallest safe change.
5. Run compile checks.
6. Do not deploy unless the current approved stage requires it.
7. Show proof.

Do not use live paid APIs during inspection or page load.
