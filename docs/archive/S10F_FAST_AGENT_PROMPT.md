@docs/AI_JOB_AGENT_5_UIUX_Handoff.md
@docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
@docs/S10_API_CONTRACT_MATRIX.md
@docs/S10_DOC5_PARITY_TRACKER.md

Proceed with S10-F only: Budget Reactor and Live Action Guard.

Agent strategy for speed:
1. Use @s10-doc-parity-planner for exact S10-F requirements.
2. Use @s10-codebase-investigator for current budget/API/render structure.
3. After edits, use @s10-ui-safety-auditor.
4. Use @s10-accessibility-reviewer only if you changed modal, drawer, focus, keyboard, or confirmation behavior.

Do not deploy.
Do not move to S10-G.
Do not move to S11 or S12.
Do not touch secrets.
Do not print secrets.
Do not call live external provider APIs.
Do not burn SerpAPI.
Do not trigger /api/ingest.
Do not call live /api/jobs on boot.
Do not fake jobs, metrics, charts, provider status, history, budget, evidence, or AI claims.

S10-F objective:
Implement the Budget Reactor and Live Action Guard. The UI must clearly distinguish safe boot, cached data, dry-run planning, live discovery, budget-guarded state, blocked state, missing usage data, and backend gaps.

Allowed files:
- web/templates/index.html
- web/static/js/api.js
- web/static/js/state.js
- web/static/js/render_budget.js
- web/static/js/render_overview.js
- web/static/js/tabs.js
- web/static/css/components.css
- web/static/css/layout.css
- docs/S10_DOC5_PARITY_TRACKER.md if updating S10-F status only

Forbidden:
- No backend rewrite.
- No new backend endpoints.
- No fake quota numbers.
- No fake budget usage.
- No fake provider cost.
- No hidden live discovery.
- No /api/ingest reference in frontend.
- No generic API_URLS.jobs.
- No direct live /api/jobs fetch on boot.
- No live discovery unless clearly behind explicit user action and budget warning.

Required S10-F behavior:
- Budget panel uses real /api/usage fields where present.
- Missing total_searches_left or monthly_usage renders Unavailable.
- Dry-run path is labeled safe and visually distinct.
- Live discovery path is disabled or guarded unless explicit user action confirms it.
- Live action copy must state: "May use discovery provider budget."
- Safe boot copy must state: "Opening this dashboard does not run live discovery."
- Budget states must exist:
  - safe
  - dry_run
  - live
  - cached
  - budget_guarded
  - blocked
  - not_configured
  - partial
  - failed
- If dry-run plan endpoint is missing or placeholder, render dry-run unavailable instead of fake plan.
- Filter changes must not spend provider budget.
- Opening the dashboard must not spend provider budget.
- LLM providers remain reasoning/classification only, never discovery.

Before editing:
1. Restate S10-F objective.
2. Summarize agent findings.
3. List files inspected.
4. List files you will change.
5. Confirm forbidden actions.

After editing:
1. Files inspected.
2. Files changed.
3. Budget reactor implemented.
4. Live action guard implemented.
5. Budget states implemented.
6. Safety proof.
7. Fake-data proof.
8. Accessibility note if relevant.
9. Backend/API gaps still remaining.
10. Stop before S10-G.
