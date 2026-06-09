# Codex to Claude Handoff — Job Hunter Pro

## Immediate state

Codex was used through OpenAI Codex CLI because Claude usage/model access was unstable. Codex hit bubblewrap/proot sandbox issues, then a proof-runner issue was found and fixed.

The confirmed useful fix so far:

- `.claude/scripts/proof_runner.py` now inserts the repo root into `sys.path` before importing `app`.
- This fixed the false proof failure: `No module named 'app'`.
- Safe local proof passed after that fix:
  - `/` returned 200
  - `/api/providers` returned 200
  - `/api/health` returned 200
  - `/api/jobs?dry_run=1` returned 200
  - dry_run=true confirmed
  - `/api/_surface` showed `placeholder_blueprint_registered=False`

## What Claude must do next

Do not continue the shallow Codex path. Claude must do the real document/spec reconciliation.

Michael clarified that Documents 1–6 may themselves contain contradictions and mistakes. Claude must not blindly obey raw documents. Claude must:

1. Audit Documents 1–6 against each other.
2. Find contradictions, stale requirements, superseded plans, fake/stub assumptions, and bad earlier directions.
3. Build `.claude/context/DOCUMENT_CONTRADICTION_MATRIX.md`.
4. Build `.claude/context/CANONICAL_RESOLVED_SPEC.md`.
5. Treat Document 5 as high authority for UI/UX, but still reconcile it against all other docs and current code.
6. Compare current code against the resolved canonical spec, not against one raw document.
7. Identify stubs/placeholders/boilerplate/fake wiring/dead routes/disconnected providers.
8. Produce a patch plan before app-logic edits.
9. Patch only proven defects.
10. Run compile, safe proof, diff checks, and stop before commit/push/deploy unless Michael explicitly commands.

## Hard rules

- Do not print secrets.
- Do not hardcode secrets.
- Do not call `/api/ingest`.
- Do not call live `/api/jobs`.
- Do not deploy unless Michael explicitly says deploy.
- Do not push unless Michael explicitly says push.
- LLM APIs are enrichment/classification only.
- Discovery providers are SerpAPI Jobs, SerpAPI Organic, Adzuna, USAJobs, Jooble, Careerjet, The Muse, and Google Places/opportunities.
- No live provider calls on page load.
- Compile and safe proof before commit/deploy decisions.
