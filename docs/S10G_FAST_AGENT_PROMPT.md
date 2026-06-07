@docs/AI_JOB_AGENT_5_UIUX_Handoff.md
@docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
@docs/S10_API_CONTRACT_MATRIX.md
@docs/S10_DOC5_PARITY_TRACKER.md

Proceed with S10-G only: Charts From Real Data Only.

Fast agent strategy:
1. Use @s10-doc-parity-planner for exact S10-G chart requirements.
2. Use @s10-codebase-investigator for current chart/render/data structure.
3. After edits, use @s10-ui-safety-auditor.
4. Use @s10-accessibility-reviewer only if chart controls, keyboard behavior, chart table fallbacks, or focus behavior are changed.

Do not deploy.
Do not move to S10-H.
Do not move to S11 or S12.
Do not touch secrets.
Do not print secrets.
Do not call live external provider APIs.
Do not burn SerpAPI.
Do not trigger /api/ingest.
Do not call live /api/jobs on boot.
Do not fake jobs, metrics, charts, provider status, history, budget, evidence, pipeline activity, or AI claims.

S10-G objective:
Implement chart shells and real-data-only chart renderers. Charts must render only from real available payload data already in AppState/cache. If real data is missing, each chart must show an honest no-data/unavailable state. No demo arrays. No static fake values. No random values.

Allowed files:
- web/templates/index.html
- web/static/js/charts.js
- web/static/js/render_history.js
- web/static/js/render_budget.js
- web/static/js/render_debug_evidence.js
- web/static/js/render_overview.js
- web/static/js/state.js only if chart state helpers are needed
- web/static/js/api.js only if safe helper expansion is needed
- web/static/css/charts.css
- web/static/css/components.css
- docs/S10_DOC5_PARITY_TRACKER.md if updating S10-G status only

Forbidden:
- No backend rewrite.
- No new backend endpoints.
- No chart demo data.
- No hardcoded chart metrics.
- No Math.random.
- No fake provider mix.
- No fake budget numbers.
- No fake accepted/rejected counts.
- No fake pipeline funnel.
- No fake industry distribution.
- No fake review distribution.
- No live discovery.
- No /api/ingest reference in frontend.
- No generic API_URLS.jobs.
- No direct live /api/jobs fetch.

Required charts:
1. pipeline funnel
2. provider mix
3. budget usage
4. accepted over time
5. rejection distribution
6. industry distribution
7. opportunity categories
8. review rating distribution
9. budget per batch where real batch budget exists
10. top-three evidence comparison where real why-three data exists

Required chart behavior:
- Every chart has a data-required check.
- Every chart has a no-data/unavailable state.
- Every chart has a short explanation of which fields are missing.
- Charts use existing real payload fields only.
- Charts tolerate placeholder backend payloads.
- Charts tolerate empty arrays.
- Charts do not crash on null/partial data.
- Charts do not call backend endpoints on their own.
- Chart rendering must be local only.
- If a table fallback is simple, add one. If not, mark table fallback as S10-L accessibility follow-up.

Before editing:
1. Restate S10-G objective.
2. Summarize fast-agent findings.
3. List files inspected.
4. List files you will change.
5. Confirm forbidden actions.

After editing:
1. Files inspected.
2. Files changed.
3. Charts implemented.
4. Which charts render from real data now.
5. Which charts show no-data/backend-gap states.
6. Safety proof.
7. Fake-data proof.
8. Accessibility/table-fallback notes.
9. Backend/API gaps still remaining.
10. Stop before S10-H.
