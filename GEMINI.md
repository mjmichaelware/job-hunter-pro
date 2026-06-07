# Job Hunter Pro — Standing Rules (S10)

Authoritative S10 UI/UX spec: docs/AI_JOB_AGENT_5_UIUX_Handoff.md. It is binding.
Read it in full each session via @ before acting. Do not work from memory or summary.

## Scope
- S10 web/UI layer only. Do not start S11/S12. Do not deploy.
- S0–S9 backend exists. Do not rewrite it.
- If a backend gap blocks the UI, report it honestly. Do not fake UI data to paper over it.

## Hard constraints
- No secrets in code, output, URLs, or logs.
- No live external API calls and no SerpAPI spend on page load.
- /api/jobs live and /api/ingest are never called on boot.
- Live discovery is explicit user action only, behind a budget warning.
- Zero fabricated data: no demo jobs, companies, metrics, charts, provider status, history, evidence, or budget numbers.
- Empty, missing, blocked, stale, cached, and not-configured states must render honestly.

## Source truth
- Discovery providers: SerpAPI, Adzuna, USAJobs, Jooble, Careerjet, The Muse, plus any already configured in the repo.
- LLM providers: OpenAI, Gemini, Claude, Groq, xAI, and similar models are reasoning, enrichment, scoring, and classification only. They are never job discovery sources.

## Tool use
- Read-only navigation tools are allowed, including search_file_content, glob, and read_file.
- Grep/search_file_content is allowed for finding frontend entrypoints and proving boot paths.
- Do not use whole-directory reads that may truncate. Read specific files or specific globs.
- Preserve existing working files.
- Edits must stay inside S10 UI/web scope unless direct inspection proves a tiny compatibility fix is required.
