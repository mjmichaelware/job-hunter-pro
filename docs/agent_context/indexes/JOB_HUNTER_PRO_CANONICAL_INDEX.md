# Job Hunter Pro — Canonical Context Index

Local index of canonical/project-context documents. Read top-down.

## Current truth (read first)
- `docs/agent_context/canonical/JOB_HUNTER_PRO_REPAIR_V2_UPDATE.md`
  — Repair v2: broad-by-default discovery, no hidden filters, honest
  rejected/unresolved visibility, provider quarantine/disable, cost honesty,
  decoupled service layer. **This supersedes older food-service-centric notes
  for the jobs flow.**

## Architecture & blueprint
- `CLAUDE.md` / `.claude/CLAUDE.md` — operating rules (secrets, safe-boot,
  deploy gating, provider law).
- `.claude/context/PROJECT_DIGEST.md` — durable digest.
- `.claude/context/AI_JOB_AGENT_1..6` — original handoff/blueprint/UX docs.
- `README.md` — master blueprint and metadata.

## Jobs-path code map (active)
- Entry: `app.py` (serves `web/` cockpit; proxies `/api/*` to `api.index`).
- Backend: `api/index.py` (jobs, debug, opportunities, history, ingest).
- Modular routes: `api/providers.py`, `api/industries.py`, `api/applications.py`,
  `api/ingest.py`.
- Discovery: `search/live_provider_bridge.py`, `providers/` (search + reasoning).
- Service layer: `config/search_taxonomy.py`, `services/query_builder.py`,
  `services/provider_status.py`, `services/filtering.py`,
  `services/job_aggregator.py`.
- Taxonomy: `industries/` (per-domain queries + terms).
- Frontend: `web/templates/index.html`, `web/static/js/*`, `web/static/css/*`.
