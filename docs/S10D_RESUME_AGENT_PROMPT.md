@docs/AI_JOB_AGENT_5_UIUX_Handoff.md
@docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
@docs/S10_API_CONTRACT_MATRIX.md
@docs/S10_DOC5_PARITY_TRACKER.md

Resume S10-D only: Advanced Filter System.

The previous S10-D run was cancelled after partial edits to:
- web/static/js/api.js
- web/static/js/render_overview.js
- web/templates/index.html

Do not restart from scratch.
Inspect the current partial edits and finish S10-D.

Use read-only agents before continuing:
- @s10-doc-parity-planner for exact S10-D requirements.
- @s10-codebase-investigator for current filter/state/render structure.
- @s10-ui-safety-auditor for safety constraints.
- @s10-accessibility-reviewer for keyboard/focus/filter drawer review.

Do not deploy.
Do not move to S10-E.
Do not move to S11 or S12.
Do not touch secrets.
Do not print secrets.
Do not call live external provider APIs.
Do not burn SerpAPI.
Do not trigger /api/ingest.
Do not call live /api/jobs on boot.
Do not fake jobs, metrics, charts, provider status, history, budget, evidence, or AI claims.

Allowed files:
- web/templates/index.html
- web/static/js/state.js
- web/static/js/filters.js
- web/static/js/render_jobs.js
- web/static/js/render_opportunities.js
- web/static/js/render_history.js
- web/static/js/render_providers.js
- web/static/js/render_budget.js
- web/static/js/api.js only if helper expansion is needed
- web/static/css/components.css
- web/static/css/layout.css
- docs/S10_DOC5_PARITY_TRACKER.md if updating S10-D status only

Forbidden:
- No backend rewrite.
- No new backend endpoints.
- No fake filter options from nonexistent data.
- No sample job data.
- No fake provider status.
- No live discovery.
- No /api/ingest reference in frontend.
- No generic API_URLS.jobs.
- No direct live /api/jobs fetch.

Required S10-D filters:

Always-visible:
1. search mode
2. radius/location
3. industry
4. provider
5. status
6. sort
7. min match score

Advanced drawer:
1. max walk minutes
2. max transit minutes
3. min rating
4. min review score
5. job type
6. pay hint
7. remote/onsite
8. provider include/exclude
9. batch
10. time range
11. rejection reason
12. classification confidence
13. place status
14. application state
15. duplicate state

Required behavior:
- Applied filter chips.
- Remove single chip.
- Reset all filters.
- Active filter count.
- Disabled/unavailable state when a filter depends on missing backend fields.
- Local filtering only.
- No provider spend on filter changes.
- No backend call on every filter change.
- Filters work across jobs, opportunities, and history where relevant.
- Filter drawer is keyboard reachable.
- Existing S10-C safe payload helpers are preserved.

Before editing:
1. Restate that this is a resume of partial S10-D.
2. Summarize what is already partially changed.
3. Summarize read-only agent findings.
4. List exact files you will change.
5. Confirm forbidden actions.

After editing:
1. Files inspected.
2. Files changed.
3. Filter system implemented.
4. Active filters vs disabled/unavailable filters.
5. Safety proof.
6. Fake-data proof.
7. Accessibility notes.
8. Stop before S10-E.
