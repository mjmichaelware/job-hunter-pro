@docs/AI_JOB_AGENT_5_UIUX_Handoff.md
@docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
@docs/S10_API_CONTRACT_MATRIX.md
@docs/S10_DOC5_PARITY_TRACKER.md

Repair S10-K/L/M only. The previous KLM local proof failed. Do not proceed to S11. Do not claim S10 complete until the failures below are fixed and documented.

MANDATORY AGENT ORDER:
1. Ask @s10-ui-safety-auditor to inspect the current failed KLM state and list exact fixes.
2. Ask @s10-accessibility-reviewer to inspect accessibility/language failures and list exact fixes.
3. Ask @s10-codebase-investigator to inspect the specific failed files and confirm current structure.
4. Ask @s10-doc-parity-planner to verify K/L/M requirements from Document 6.
5. Only after all read-only agents report, make edits.

FAILED LOCAL PROOF ITEMS TO FIX:

A. Safety failure:
- web/static/js/render_overview.js line around 12 contains generic API_URLS.jobs fetch:
  safeFetch(API_URLS.jobs)
- This must be removed or replaced with safe dry-run/manual-only logic.
- There must be no API_URLS.jobs constant/generic jobs fetch path.
- There must be no live /api/jobs on boot.

B. Ambient fake-data proof failure:
- web/static/js/ambient.js uses Math.random().
- For this project proof gate, Math.random is banned because fake/random motion can look like fake telemetry.
- Replace with deterministic ambient positions or disable ambient randomness.
- Ambient visual must be idle/decorative only, no fake activity.

C. S10-K PWA/offline failure:
- Missing required stale label/term.
- Add explicit stale/cached/offline state copy.
- Offline cache must not fake cached history.
- Service worker must not cache /api/jobs, /api/ingest, or SerpAPI paths.

D. S10-L accessibility failure:
- Missing aria-live term.
- Add appropriate aria-live status region(s), especially for offline/budget/pipeline or app status.
- Do not overclaim language support.
- English primary. Spanish only for explicit static UI labels if implemented. Russian optional/future/unavailable only.

E. S10-M final document failure:
- Missing docs/S10_FINAL_PARITY_GATE.md.
- Create it.
- It must document all S10 sessions A-M, safety proof, no-deploy, no-fake, backend gaps, and remaining limitations honestly.
- It must not say "full Document 5 parity achieved" unless every local proof passes and backend gaps are honestly scoped.
- Prefer wording: "S10 local UI parity gate passed with documented backend gaps" only after repair.

Global forbidden actions:
- Do not deploy.
- Do not move to S11 or S12.
- Do not touch secrets.
- Do not print secrets.
- Do not call live external provider APIs.
- Do not burn SerpAPI.
- Do not trigger /api/ingest.
- Do not call live /api/jobs on boot.
- Do not fake cached history, offline data, metrics, charts, pipeline events, Markov probabilities, map pins, provider status, or AI claims.
- Do not add external CDN libraries.

Allowed files:
- web/templates/index.html
- web/static/js/api.js
- web/static/js/render_overview.js
- web/static/js/ambient.js
- web/static/js/offline.js
- web/static/js/state.js
- web/static/js/tabs.js
- web/static/js/charts.js
- web/static/sw.js
- web/static/manifest.json
- web/static/css/base.css
- web/static/css/components.css
- docs/S10_DOC5_PARITY_TRACKER.md
- docs/S10_FINAL_PARITY_GATE.md
- docs/S10KLM_REPAIR_AGENT_PROMPT.md

Required edits:
1. Remove generic API_URLS.jobs boot fetch risk.
2. Remove Math.random from ambient.js or make ambient deterministic/static.
3. Add stale/offline/cached labels.
4. Add aria-live status region.
5. Create docs/S10_FINAL_PARITY_GATE.md.
6. Update tracker honestly.
7. Stop after KLM repair. Do not start S11.

After editing, final response must include:
1. Agent findings summarized.
2. Files changed.
3. Exact fixes for each failed proof item A-E.
4. Safety proof.
5. Fake-data proof.
6. Accessibility proof.
7. Final doc proof.
8. Stop before S11/S12.
