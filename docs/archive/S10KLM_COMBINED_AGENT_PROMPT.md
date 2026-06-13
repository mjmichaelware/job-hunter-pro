@docs/AI_JOB_AGENT_5_UIUX_Handoff.md
@docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
@docs/S10_API_CONTRACT_MATRIX.md
@docs/S10_DOC5_PARITY_TRACKER.md

Proceed with S10-K, S10-L, and S10-M together as one sequential closing run.

Important sequencing:
1. Complete S10-K first: PWA and Offline History.
2. Then complete S10-L: Accessibility, Bilingual, Keyboard.
3. Then complete S10-M: Final S10 Parity Gate.
4. Do not skip any section.
5. Do not deploy.

Agent strategy for speed:
- Use @s10-doc-parity-planner once at the beginning for K/L/M requirements.
- Use @s10-codebase-investigator once at the beginning for current frontend/docs structure.
- Use @s10-accessibility-reviewer only for S10-L and S10-M.
- Use @s10-ui-safety-auditor after all edits and before final summary.
- Do not use generalist unless you need read-only investigation of a large file set.
- Agents are read-only. Main Gemini agent performs edits.

Global forbidden actions:
- Do not deploy.
- Do not move to S11 or S12.
- Do not touch secrets.
- Do not print secrets.
- Do not call live external provider APIs.
- Do not burn SerpAPI.
- Do not trigger /api/ingest.
- Do not call live /api/jobs on boot.
- Do not fake jobs, metrics, charts, provider status, history, budget, evidence, maps, pins, commute data, review ratings, pipeline activity, cached history, offline data, translations, or AI claims.
- Do not add fake PWA cache entries.
- Do not pretend offline mode has live provider access.
- Do not add external CDN libraries.

Allowed files for combined K/L/M:
- web/templates/index.html
- web/static/manifest.webmanifest
- web/static/service-worker.js
- web/static/js/pwa.js
- web/static/js/offline_store.js
- web/static/js/state.js
- web/static/js/tabs.js
- web/static/js/api.js only if safe helper expansion is needed
- web/static/js/render_history.js
- web/static/js/render_overview.js
- web/static/js/render_budget.js
- web/static/js/render_debug_evidence.js
- web/static/js/charts.js
- web/static/css/base.css
- web/static/css/layout.css
- web/static/css/components.css
- web/static/css/charts.css
- docs/S10_DOC5_PARITY_TRACKER.md
- docs/S10_FINAL_PARITY_GATE.md

================================================================================
S10-K: PWA and Offline History
================================================================================

Objective:
Add a safe PWA/offline shell for cached history only.

Required behavior:
- Add manifest if missing.
- Add service worker only for static asset shell and safe cache behavior.
- Add IndexedDB/offline store helper for safe history/batch payloads.
- Offline mode may show cached history only.
- Offline mode must clearly label cached/stale data.
- Offline mode must not pretend providers are live.
- Offline mode must not call live discovery.
- Offline mode must not fake cached history.
- Register service worker only if supported.
- If IndexedDB is unavailable, render offline storage unavailable.
- If no cached history exists, render empty offline state.

Required S10-K proof:
- manifest exists.
- service worker exists.
- offline store helper exists.
- offline/cached/stale labels exist.
- no fake cached history.
- no live sync on boot.

================================================================================
S10-L: Accessibility, Bilingual, Keyboard
================================================================================

Objective:
Make the cockpit usable, accessible, keyboard-safe, and honest about language support.

Required accessibility behavior:
- Tabs are keyboard reachable.
- Filter drawer is keyboard reachable.
- Evidence drawer is keyboard reachable.
- Budget live action confirmation is keyboard reachable.
- Escape closes drawers/modals where applicable.
- Focus returns to triggering element where practical.
- Focus-visible states are obvious.
- Buttons are real buttons where possible.
- Important status regions use aria-live where state changes dynamically.
- Charts have named no-data states and accessible descriptions.
- No color-only status.
- Reduced motion is respected.
- Touch targets are reasonable.
- Semantic headings are preserved.

Required bilingual behavior:
- English primary.
- Spanish display only where source fields or explicit labels exist.
- Do not invent machine translations.
- If bilingual support is not fully implemented, render “language support unavailable” or document as backend/future gap.
- Russian remains optional future only unless real source support exists.

Required S10-L proof:
- keyboard/focus controls exist.
- aria labels/live regions exist for key state.
- no unsupported language claims.
- no color-only status.

================================================================================
S10-M: Final S10 Parity Gate
================================================================================

Objective:
Close S10 locally and document remaining backend gaps honestly.

Create or update:
- docs/S10_FINAL_PARITY_GATE.md
- docs/S10_DOC5_PARITY_TRACKER.md

Required final proof sections:
1. Document proof:
   - Document 5 exists.
   - Document 6 exists.
   - API contract matrix exists.
   - Parity tracker exists.
2. Session proof:
   - S10-A completed.
   - S10-B completed.
   - S10-C completed.
   - S10-D completed.
   - S10-E completed.
   - S10-F completed.
   - S10-G completed.
   - S10-H completed.
   - S10-I completed.
   - S10-J completed.
   - S10-K completed or explicitly marked partial with reason.
   - S10-L completed or explicitly marked partial with reason.
   - S10-M completed locally.
3. UI proof:
   - 8 tabs exist.
   - Advanced filters exist.
   - Evidence drawer exists.
   - Budget guard exists.
   - Real-data-only charts exist.
   - Pipeline no-fake readiness exists.
   - Geo/review unavailable states exist.
   - PWA/offline safe shell exists if implemented.
   - Accessibility readiness exists.
4. Safety proof:
   - no frontend /api/ingest
   - no generic API_URLS.jobs
   - no direct live /api/jobs fetch on boot
   - no fake/demo frontend terms
   - no fake chart arrays
   - no fake cached history
   - no fake Markov probabilities
   - no fake pipeline stream
   - no external map/geocoding calls
   - no secrets
   - no deploy
5. Backend gap proof:
   - missing or partial provider status
   - missing or partial industries
   - missing or partial why-three
   - missing or partial evidence fields
   - missing or partial budget fields
   - missing or partial dry-run query plan
   - missing SSE endpoint
   - missing review component breakdown
   - missing place resolution notes
   - missing commute/radius fields
   - missing real offline history contract if applicable

Important:
S10-M may mark S10 locally complete only if K and L are implemented honestly and all proof gates pass. If not, document exact remaining gaps and do not claim full S10 completion.

Before editing:
1. Restate combined K/L/M objective.
2. Summarize read-only agent findings.
3. List files inspected.
4. List files you will change.
5. Confirm forbidden actions.

After S10-K:
1. State K files changed.
2. State K proof.

After S10-L:
1. State L files changed.
2. State L proof.

After S10-M:
1. State final files changed.
2. State final S10 parity result.
3. State remaining backend gaps.
4. State safety proof.
5. State fake-data proof.
6. Stop. Do not deploy.
