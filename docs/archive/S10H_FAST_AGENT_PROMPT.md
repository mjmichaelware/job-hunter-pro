@docs/AI_JOB_AGENT_5_UIUX_Handoff.md
@docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
@docs/S10_API_CONTRACT_MATRIX.md
@docs/S10_DOC5_PARITY_TRACKER.md

Proceed with S10-H only: Pipeline Reactor / SSE Readiness.

Fast agent strategy:
1. Use @s10-doc-parity-planner for exact S10-H requirements.
2. Use @s10-codebase-investigator for current debug/pipeline/chart/render structure.
3. After edits, use @s10-ui-safety-auditor.
4. Use @s10-accessibility-reviewer only if pipeline controls, focus, live region, or keyboard behavior are changed.

Do not deploy.
Do not move to S10-I.
Do not move to S11 or S12.
Do not touch secrets.
Do not print secrets.
Do not call live external provider APIs.
Do not burn SerpAPI.
Do not trigger /api/ingest.
Do not call live /api/jobs on boot.
Do not fake jobs, metrics, charts, provider status, history, budget, evidence, pipeline activity, stream events, or AI claims.

S10-H objective:
Prepare the UI for pipeline telemetry without faking live activity. If no SSE endpoint exists, render a clear "pipeline stream unavailable" state and use only real last-batch/static evidence when available.

Allowed files:
- web/templates/index.html
- web/static/js/render_debug_evidence.js
- web/static/js/charts.js
- web/static/js/state.js
- web/static/js/tabs.js
- web/static/js/api.js only if safe helper expansion is needed
- web/static/css/components.css
- web/static/css/charts.css
- docs/S10_DOC5_PARITY_TRACKER.md if updating S10-H status only
- docs/S10_BACKEND_GAPS.md if documenting missing SSE/backend gap

Forbidden:
- No backend rewrite.
- No new backend SSE endpoint.
- No fake event stream.
- No synthetic pipeline counts.
- No fake live activity.
- No animated counts without data.
- No live discovery.
- No /api/ingest reference in frontend.
- No generic API_URLS.jobs.
- No direct live /api/jobs fetch.

Required pipeline stages:
1. discover
2. normalize
3. resolve_place
4. classify
5. score
6. filter
7. dedupe
8. store

Required rejection shedding reasons:
- not_food_service
- outside_radius
- ambiguous_place_resolution
- duplicate
- budget guard
- provider error
- missing source URL
- transit unavailable
- low confidence fit
- low rating cap
- place resolution unavailable

Required behavior:
- Pipeline UI exists.
- No-stream idle state exists.
- SSE unavailable/backend-gap state exists if no endpoint exists.
- If static last-batch evidence exists, render it honestly.
- If no real data exists, show no-data explanation.
- No fake pipeline animation or fake counts.
- No network stream connects on boot unless endpoint is safe and explicitly documented.
- ARIA live region exists if status text changes dynamically.

Before editing:
1. Restate S10-H objective.
2. Summarize fast-agent findings.
3. List files inspected.
4. List files you will change.
5. Confirm forbidden actions.

After editing:
1. Files inspected.
2. Files changed.
3. Pipeline reactor readiness implemented.
4. SSE/backend gap behavior.
5. Static evidence behavior.
6. Safety proof.
7. Fake-data proof.
8. Accessibility/live-region notes.
9. Backend/API gaps still remaining.
10. Stop before S10-I.
