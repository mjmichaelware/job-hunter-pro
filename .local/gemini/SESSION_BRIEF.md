# SESSION_BRIEF.md

## Project
Job Hunter Pro

## Environment
- Android ARM64 Termux
- Flask app
- Google Cloud Run target
- Secrets must stay in Secret Manager only

## Non-negotiables
- Never hardcode or print secrets
- Never guess or patch blindly
- Compile locally before any deploy
- After deploy, check /api/health, then logs if needed
- LLM providers are enrichment/classification only
- Discovery providers are SerpAPI, Adzuna, USAJobs, Jooble, Careerjet, The Muse
- Never burn SerpAPI on page load
- /api/ingest must be Cloud Scheduler OIDC only
- Do not deploy until S12

## Current stage status
- S0 complete
- S1 complete
- S2 complete
- S3 complete

## Architecture locks
- Recall-first discovery
- Industries are hints/cues/seeds, not hard early exclusion gates
- S2 stays simple/declarative
- S3 providers are fetch/enrichment boundaries only
- S6 owns scoring/classification
- S7 owns broad recall mode and budget orchestration
- LLMs never perform job discovery
- Two-phase filtering:
  - early cheap filters after normalization
  - late expensive filters after enrichment

## Working style
- No progress narration
- No “thinking out loud”
- No repeating the task back
- No long explanations
- Show only:
  1. smallest safe change set
  2. exact changed files
  3. proof commands/results
  4. stop

## Current instruction
Read GEMINI.md and this file first, then inspect only the files needed for the requested stage.
