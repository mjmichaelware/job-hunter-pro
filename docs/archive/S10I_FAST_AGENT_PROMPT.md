@docs/AI_JOB_AGENT_5_UIUX_Handoff.md
@docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
@docs/S10_API_CONTRACT_MATRIX.md
@docs/S10_DOC5_PARITY_TRACKER.md

Proceed with S10-I only: Geo Radar and Review Geometry.

Fast agent strategy:
1. Use @s10-doc-parity-planner for exact S10-I requirements.
2. Use @s10-codebase-investigator for current job/opportunity geo/review field usage.
3. After edits, use @s10-ui-safety-auditor.
4. Use @s10-accessibility-reviewer only if map-like controls, focus behavior, keyboard behavior, or status announcements are changed.

Do not deploy.
Do not move to S10-J.
Do not move to S11 or S12.
Do not touch secrets.
Do not print secrets.
Do not call live external provider APIs.
Do not burn SerpAPI.
Do not trigger /api/ingest.
Do not call live /api/jobs on boot.
Do not fake jobs, metrics, charts, provider status, history, budget, evidence, maps, pins, commute data, review ratings, or AI claims.

S10-I objective:
Implement geo radar and review-trust UI components using only real fields already returned in job/opportunity payloads. Missing geo/review fields must render Unavailable. Do not invent map pins, commute durations, coordinates, ratings, review counts, or review scores.

Allowed files:
- web/templates/index.html
- web/static/js/render_jobs.js
- web/static/js/render_opportunities.js
- web/static/js/render_debug_evidence.js
- web/static/js/charts.js
- web/static/js/state.js only if geo/review state helpers are needed
- web/static/js/api.js only if safe helper expansion is needed
- web/static/css/components.css
- web/static/css/charts.css
- docs/S10_DOC5_PARITY_TRACKER.md if updating S10-I status only

Forbidden:
- No backend rewrite.
- No new backend endpoints.
- No fake map.
- No fake pins.
- No fake commute.
- No fake rating.
- No fake review score.
- No geocoding call.
- No Google Maps call.
- No live discovery.
- No /api/ingest reference in frontend.
- No generic API_URLS.jobs.
- No direct live /api/jobs fetch.

Required geo data points:
- origin address
- resolved address
- place id
- lat/lng if returned
- radius miles
- distance
- walk duration
- transit duration
- drive duration
- place status
- ambiguous place resolution
- outside radius
- unavailable commute

Required review intelligence data points:
- rating
- review count
- sentiment if real
- consistency if real
- review score
- low rating cap
- 60/15/15/10 review formula concept

Required behavior:
- Jobs/opportunities with missing geo show Unavailable.
- Jobs/opportunities with returned geo show real distance/radius/commute only.
- Ambiguous place has a dedicated state.
- Outside radius has a dedicated state.
- Review gauge respects returned values.
- Review gauge cannot imply unsupported score.
- Low rating cap explanation renders only if real rating/review fields support it.
- No map pins without coordinates.
- If no coordinates exist, render a radar/list view instead of a map.
- No external map or geocoding scripts.

Before editing:
1. Restate S10-I objective.
2. Summarize fast-agent findings.
3. List files inspected.
4. List files you will change.
5. Confirm forbidden actions.

After editing:
1. Files inspected.
2. Files changed.
3. Geo radar implemented.
4. Review trust geometry implemented.
5. Missing-field behavior.
6. Safety proof.
7. Fake-data proof.
8. Accessibility notes if relevant.
9. Backend/API gaps still remaining.
10. Stop before S10-J.
