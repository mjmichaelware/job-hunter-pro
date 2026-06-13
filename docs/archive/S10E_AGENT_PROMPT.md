@docs/AI_JOB_AGENT_5_UIUX_Handoff.md
@docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
@docs/S10_API_CONTRACT_MATRIX.md
@docs/S10_DOC5_PARITY_TRACKER.md

Proceed with S10-E only: Evidence Drawer System.

Use read-only agents before editing:
1. @s10-doc-parity-planner for exact S10-E requirements.
2. @s10-codebase-investigator for current renderer/state/template structure.
3. @s10-ui-safety-auditor for safety constraints.
4. @s10-accessibility-reviewer for drawer keyboard/focus recommendations.

Do not deploy.
Do not move to S10-F.
Do not move to S11 or S12.
Do not touch secrets.
Do not print secrets.
Do not call live external provider APIs.
Do not burn SerpAPI.
Do not trigger /api/ingest.
Do not call live /api/jobs on boot.
Do not fake jobs, metrics, charts, provider status, history, budget, evidence, or AI claims.

S10-E objective:
Implement the Evidence Drawer System using only fields returned by real payloads or explicitly unavailable states. Missing evidence fields must render as Unavailable. Do not invent evidence.

Allowed files:
- web/templates/index.html
- web/static/js/state.js
- web/static/js/render_debug_evidence.js
- web/static/js/render_jobs.js
- web/static/js/render_opportunities.js
- web/static/js/render_history.js
- web/static/js/api.js only if helper expansion is needed
- web/static/css/components.css
- web/static/css/layout.css
- docs/S10_DOC5_PARITY_TRACKER.md if updating S10-E status only

Mandatory evidence fields:
- raw_title
- normalized_title
- company
- source
- provider_id
- industry_scores
- accepted/rejected status
- rejection_reasons
- dedupe_key
- place_resolution
- review_score
- match_score
- budget_cost
- query_seed
- discovery_mode
- timestamp

Required drawer behavior:
- Job cards can open evidence drawer.
- Opportunity cards can open evidence drawer where data exists.
- History/debug rows can expose evidence where data exists.
- Drawer has close button.
- Escape closes drawer.
- Focus moves into drawer when opened.
- Focus returns to triggering element when closed.
- Missing fields render Unavailable.
- Raw-vs-normalized comparison exists.
- Rejection reasons render only if returned.
- Dedupe key renders only if returned.
- Budget cost renders only if returned.
- No generic “AI decided” explanation.
- No hidden JSON dump as primary UI.

Before editing:
1. Restate S10-E objective.
2. Summarize read-only agent findings.
3. List files you will inspect.
4. List files you will change.
5. Confirm forbidden actions.

After editing:
1. Files inspected.
2. Files changed.
3. Evidence drawer system implemented.
4. Evidence fields supported.
5. Missing-field behavior.
6. Safety proof.
7. Fake-data proof.
8. Accessibility notes.
9. Backend gaps still remaining.
10. Stop before S10-F.
