You are working inside the Job Hunter Pro Flask repository on Android ARM64 Termux.

Owner: Michael Ware
Project ID: ai-job-agent-498702
Region: us-central1
Cloud Run service: job-hunter-pro
Live URL: https://job-hunter-pro-5t3wttw2ua-uc.a.run.app

MISSION:
Fix the right-side Filters UI properly. Do NOT remove filter functionality. The current live mobile view shows the filters panel consuming the right half of the screen and crushing the main dashboard. That is unacceptable.

The filters must behave like a normal responsive dashboard component:
- Desktop/tablet wide viewport: filters may be a right rail or drawer if layout has enough room.
- Mobile/narrow viewport: filters must be hidden by default.
- Mobile/narrow viewport: tapping the filters button opens a full-height off-canvas overlay/sheet.
- Mobile/narrow viewport: the overlay must sit above the app, not participate in CSS grid/flex layout, not consume a column, and not shove content sideways.
- Close button, Escape key, and outside/backdrop click should close it if those hooks exist or can be added cleanly.
- Existing filter controls must remain functional.
- Existing nav/sidebar tabs must remain functional.
- Do not disable the filters unless absolutely unavoidable.
- Do not touch secrets.
- Do not call /api/ingest.
- Do not run live job discovery.
- Do not burn SerpAPI.
- Default/safe API probes only: /api/health, /api/usage, /api/opportunities, /api/history, /api/jobs?dry_run=1.
- Do not use broad regex patches.
- Inspect before patching.
- Compile locally before deploy.
- Deploy only after S12 proof.
- After deploy, check /api/health and live HTML/CSS/JS proof.

FOLLOW THE PROJECT WORKFLOW S0 THROUGH S12. Do not skip stages.

S0 — Locate repo and baseline:
- Print pwd.
- Print git status --short.
- Confirm app.py, web/templates/index.html, web/static/css/base.css, web/static/css/layout.css, and web/static/js/state.js exist.
- Do not proceed if repo root is wrong.

S1 — Inspect the actual UI wiring:
Run and review:
grep -Rni "filter-drawer\|toggle-filters\|filter-count\|drawer\|filters\|evidence-drawer\|aria-hidden\|classList.*open" web/templates/index.html web/static/css web/static/js || true
sed -n '1,260p' web/templates/index.html
sed -n '1,280p' web/static/css/layout.css
sed -n '1,260p' web/static/js/state.js

S2 — Identify exact cause:
Find why the filters panel is visible in the normal layout on mobile. Likely causes:
- #filter-drawer or filters aside is in normal grid/flex flow.
- Mobile media rules do not move it off-canvas.
- .open state defaults wrong.
- toggle button exists but drawer is not positioned fixed/absolute correctly.
- z-index/transform/width rules broken.
- JS opens drawer but does not close it or does not remove .open.

S3 — Patch minimally:
Patch only the required frontend files. Likely files:
- web/static/css/layout.css
- web/static/js/state.js
- possibly web/templates/index.html only if aria/classes are wrong

Required CSS behavior:
- On narrow screens, #filter-drawer must be fixed, not grid/flex content.
- On narrow screens, #filter-drawer must default closed/off-canvas:
  transform: translateX(100%);
  pointer-events: none;
  visibility: hidden;
- On narrow screens, #filter-drawer.open must be visible:
  transform: translateX(0);
  pointer-events: auto;
  visibility: visible;
- Width should be mobile sane:
  width: min(92vw, 380px);
  max-width: 92vw;
  right: 0;
  top: 0;
  bottom: 0;
  height: 100dvh;
  overflow-y: auto;
  z-index high enough to overlay content.
- The main app grid must not allocate a column to the filter drawer on mobile.
- The toggle button must remain usable and not cover content awkwardly.
- Desktop rules must not break the dashboard.

Required JS behavior:
- toggle-filters click toggles drawer .open and aria-hidden.
- close button removes .open and sets aria-hidden true if a close button exists.
- Escape closes drawer.
- Optional backdrop/outside click closes drawer if safe.
- Do not throw null errors if any element is missing.

S4 — Do not patch blindly:
Before editing, create timestamped backups outside git tracking if possible:
mkdir -p .repair_backups
cp web/static/css/layout.css ".repair_backups/layout.css.$(date +%Y%m%d_%H%M%S)"
cp web/static/js/state.js ".repair_backups/state.js.$(date +%Y%m%d_%H%M%S)"
cp web/templates/index.html ".repair_backups/index.html.$(date +%Y%m%d_%H%M%S)"

S5 — Validate source after patch:
Run:
grep -Rni "filter-drawer\|toggle-filters\|filter-count\|classList.*open\|aria-hidden" web/templates/index.html web/static/css web/static/js || true
git diff -- web/templates/index.html web/static/css/layout.css web/static/js/state.js web/static/css/base.css

S6 — Compile:
Run:
python3 -m py_compile $(git ls-files '*.py')

S7 — Local Flask proof:
Run a Python test_client proof:
- GET / returns 200
- GET /api/health returns 200
- GET /static/css/layout.css returns 200
- GET /static/js/state.js returns 200
- rendered HTML contains filter drawer and toggle button if they are supposed to exist
- rendered HTML still contains normal nav/sidebar tabs
- rendered HTML does not force filter drawer open by default
- /api/jobs?dry_run=1 returns a safe response or at least does not call live discovery

S8 — Static responsive proof:
Add or run a small source-level assertion that layout.css contains mobile rules for #filter-drawer closed state and #filter-drawer.open open state.
Check for:
- position: fixed
- transform: translateX(100%)
- #filter-drawer.open
- transform: translateX(0)
- width: min(92vw, 380px) or equivalent sane mobile width

S9 — Clean git:
- Do not commit backup files.
- Do not include .repair_backups in git.
- If backup files are currently tracked from earlier attempts, remove them from git in a cleanup commit only if safe.
- Show git status --short.

S10 — Commit:
Commit the frontend fix with a clean message:
git add web/templates/index.html web/static/css/layout.css web/static/js/state.js web/static/css/base.css
git commit -m "Fix responsive filters drawer layout"

If there is nothing to commit, say so and do not fake it.

S11 — Push:
git push origin main

S12 — Deploy and verify:
If the push trigger runs, monitor Cloud Build.
If a direct source deploy is needed, use the existing Cloud Run deploy pattern for this service with Secret Manager references only. Do not print secrets.
After deployment:
- Get the live service URL from Cloud Run.
- curl /api/health.
- curl / and grep for filter-drawer and toggle-filters.
- curl /static/css/layout.css and grep for #filter-drawer mobile/off-canvas rules.
- curl /static/js/state.js and grep for toggle/close behavior.
- Print the exact URL to open.

Required final output:
1. Exact files changed.
2. Exact Cloud Run URL.
3. Latest ready revision.
4. Proof that /api/health is status ok.
5. Proof that the live CSS has off-canvas closed state and .open state.
6. One sentence: "The filters are preserved; the mobile layout no longer lets the filters consume the viewport."
