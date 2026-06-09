# Final Patch Plan — Job Hunter Pro

For each confirmed defect from `BUG_LEDGER.md`: target file, intended edit, blast radius, rollback, proof command. **NO edits applied yet.** This plan must be approved by Michael before any app-logic change.

Hard rules in effect (per `CLAUDE.md` + corrected mission):
- No commits without explicit instruction.
- No push.
- No deploy.
- No `/api/ingest` call.
- No live `/api/jobs` call.
- No secrets in logs / URLs / code.
- Inspect before patching; don't blind-regex large files.

Patch order: P1 → P2 → optional P3 → optional P4 → STOP and prove. Patches P5..P-H1 are deferred to subsequent cycles unless Michael authorizes more.

---

## P1 — Restore the rejection gate AND introduce resolution_flags

**Target:** `api/index.py`
**Resolves:** `BUG_LEDGER.md` CRIT-1.
**Spec ref:** `CANONICAL_RESOLVED_SPEC.md` §6.

### Intent
Turn the silently-disabled `rejection_reasons()` into the canonical 3-way classifier:
- **Reject** (genuinely disqualified): `not_in_industry`, `ambiguous_place_resolution`, `outside_radius_X`, `transit_too_long_X`, `duplicate`, `missing_source_url`, `provider_error`, `budget_guard`.
- **Unresolved** (visible, but flagged): `address_unresolved`, `radius_unknown`, `transit_unknown`.
- **Accepted**: everything else.

### Edits

1. **Replace `rejection_reasons(job)` body (lines 626-648)** with a function returning a structured dict:
   ```python
   def classify_job(job) -> dict:
       # Returns {"reject_reasons": [...], "resolution_flags": [...]}
       hard = []
       flags = []
       food_text = " ".join([clean(job.get(k)) for k in ("title","company","description","restaurant_name","resolved_place_name")] + [" ".join(job.get("tags") or [])])

       if not is_food_text(food_text):
           hard.append("not_food_service")          # P3 will generalize to not_in_industry

       if not job.get("resolved_address"):
           flags.append("address_unresolved")        # was hard reject; now a flag
       if job.get("radius_miles") is None:
           flags.append("radius_unknown")
       elif job["radius_miles"] > Config.MAX_RADIUS_MILES:
           hard.append(f"outside_radius_{job['radius_miles']}mi")

       if job.get("commute_seconds") is None:
           flags.append("transit_unknown")
       elif job["commute_seconds"] >= Config.MAX_TRANSIT_SECONDS:
           hard.append(f"transit_too_long_{round(job['commute_seconds']/60)}min")

       if not (job.get("source_url") or job.get("apply_url")):
           flags.append("missing_source_url")        # flag (visible) not hard reject

       return {"reject_reasons": hard, "resolution_flags": flags}
   ```
   Keep the old `rejection_reasons` symbol as a thin compatibility shim that returns `classify_job(job)["reject_reasons"]` if any external test calls it (verify with `grep -n rejection_reasons` first).

2. **Update the call site in `fetch_jobs_live()` (lines 717-757)** to produce three buckets:
   ```python
   accepted, unresolved, rejected = [], [], []
   accepted_keys = set()
   for raw in raw_jobs:
       job = normalize_job(raw)
       cls = classify_job(job)
       hard, flags = cls["reject_reasons"], cls["resolution_flags"]
       if hard:
           rejected.append({...existing rejected fields..., "reasons": hard, "resolution_flags": flags})
           continue
       key = canonical_key(job)
       if key in accepted_keys:
           rejected.append({..., "reasons": ["duplicate"], "resolution_flags": flags})
           continue
       accepted_keys.add(key)
       job["resolution_flags"] = flags
       job["needs_resolution"] = bool(flags)
       if flags:
           unresolved.append(job)
       else:
           accepted.append(job)
   # sort accepted, unresolved separately
   return {
       "raw_count": len(raw_jobs),
       "query_count": query_count,
       "nearby_restaurant_count": ...,
       "accepted": accepted,
       "unresolved": unresolved,
       "rejected": rejected[:100],
       "provider_breakdown": provider_breakdown,
   }
   ```

3. **Update `/api/jobs` response (lines 1115-1155)** to expose the three buckets:
   ```python
   accepted_filtered = apply_filters(result["accepted"])
   unresolved_filtered = apply_filters(result.get("unresolved", []))
   return jsonify({
       "status": "success",
       "source": VERSION,
       "count": len(accepted_filtered),
       "unresolved_count": len(unresolved_filtered),
       "rejected_count": len(result.get("rejected", [])),
       "unfiltered_count": len(result["accepted"]),
       "raw_count": result["raw_count"],
       ...
       "data": accepted_filtered,
       "unresolved": unresolved_filtered,
       "rejected": result.get("rejected", [])[:100],
       ...
   })
   ```

4. **Update `/api/debug/jobs`** similarly to expose the unresolved bucket.

### Blast radius
- `tests/test_pipeline_reject.py`, `tests/test_api_frontend_contract.py`, `tests/test_s9_full_api_wiring.py` likely assert on the old shape. Read first; update assertions.
- Frontend `render_jobs.js` will need to render the new `unresolved` array — held until P1.5 (frontend).
- `web/static/js/render_debug_evidence.js` may already render `rejected` — verify unresolved gets rendered too.

### Proof
```
python3 -m py_compile $(git ls-files "*.py")
bash .claude/scripts/safe_local_proof.sh
PYTHONPATH=. python3 -m pytest tests/test_pipeline_reject.py tests/test_api_frontend_contract.py tests/test_s9_full_api_wiring.py -q
```
Expected: all green. `/api/jobs?dry_run=1` still passes (unchanged path). No live provider calls.

### Rollback
Single-file revert: `git checkout HEAD -- api/index.py` (assuming no commit yet).

---

## P1.5 — Frontend renders the new `unresolved` bucket

**Target:** `web/static/js/render_jobs.js`, possibly `web/static/js/state.js`, `web/templates/index.html`.
**Resolves:** completes CRIT-1 end-to-end (canonical §9).

### Intent
Live Jobs tab must show accepted jobs **and** unresolved jobs as two visible groups. Each unresolved card shows the `resolution_flags` as badges ("Address unresolved", "Transit unknown", etc.). Debug Evidence tab shows `rejected` with reasons (already partly there).

### Edits
1. In `render_jobs.js`, after rendering accepted, render an "Unresolved candidates" subheading and iterate `payload.unresolved`. Each card gets `class="unresolved"` and per-flag badges from `resolution_flags`.
2. Add minimal CSS in `web/static/css/components.css` (or wherever job card styles live) for the unresolved badge group. **Tracking note:** I'll find the exact stylesheet location at edit time — `web/static/` listing showed `css/` exists; I haven't enumerated subfiles yet. The proof step compiles + safe_local_proof exercises the static path, so a missing CSS file would surface there.
3. In `render_debug_evidence.js`, ensure rejected reasons render verbatim (no fake summarization).

### Blast radius
- `web/static/js/state.js` may need to track the new `unresolved` array for filters to operate on it.
- No backend changes.

### Proof
- `python3 -m py_compile` (unaffected).
- Open `web/templates/index.html` locally via `safe_local_proof.sh`'s served Flask, click Live Jobs → confirm visible "Unresolved" section. (No automated UI test exists yet — visual proof only.)

### Rollback
`git checkout HEAD -- web/static/js/render_jobs.js [other touched files]`.

---

## P2 — Real OIDC verification on `/api/ingest`

**Target:** `api/index.py:1183-1190`, possibly `app.py:129-138`, and `ingest/oidc.py`.
**Resolves:** `BUG_LEDGER.md` CRIT-2.
**Spec ref:** `CANONICAL_RESOLVED_SPEC.md` §11.

### Intent
Replace the Bearer-prefix-only check with a real JWT verification using `google-auth`:
- Validate signature via Google JWKS.
- Validate `aud` claim equals the Cloud Run service URL (env var `CLOUD_RUN_URL` or computed from request).
- Validate `email` equals `Config.SCHEDULER_SA_EMAIL` (new env var, defaults to `job-hunter-scheduler@ai-job-agent-498702.iam.gserviceaccount.com`).
- Reject on signature failure, audience mismatch, email mismatch, or expired token.

### Edits
1. **Read `ingest/oidc.py` first** — it almost certainly already has the right logic (constructed in S8 per Doc 4). If so, `api/index.py:verify_oidc` simply delegates:
   ```python
   from ingest.oidc import verify_oidc as _real_verify_oidc
   def verify_oidc():
       return _real_verify_oidc(request.headers.get("Authorization"), fake_claims=None)
   ```
2. If `ingest/oidc.py` is also stubbed (the `fake_claims` parameter from the earlier grep suggests it's at least partially real), implement using `google-auth`:
   ```python
   from google.oauth2 import id_token
   from google.auth.transport import requests as g_requests
   _g_request = g_requests.Request()
   def verify_oidc_header(auth_header: str, expected_audience: str, expected_email: str) -> bool:
       if not auth_header or not auth_header.startswith("Bearer "):
           return False
       token = auth_header[7:].strip()
       try:
           claims = id_token.verify_oauth2_token(token, _g_request, audience=expected_audience)
       except Exception as exc:
           logger.warning("OIDC verify failed: %s", exc)
           return False
       return claims.get("email", "") == expected_email and claims.get("email_verified") is True
   ```
3. Add `google-auth>=2.30` to `requirements.txt` (currently missing).
4. Add env vars `CLOUD_RUN_URL` (default `https://job-hunter-pro-5t3wttw2ua-uc.a.run.app/api/ingest`) and `SCHEDULER_SA_EMAIL` (default `job-hunter-scheduler@ai-job-agent-498702.iam.gserviceaccount.com`) to `Config`.

### Blast radius
- `tests/test_oidc_ingest.py` likely uses `fake_claims=...`. Verify it still injects via test path.
- New dependency on `google-auth` adds ~1.5 MB to the runtime image; acceptable.
- `app.py`'s Bearer-prefix check at line 130-138 can stay as a fast-reject (saves the proxy hop), but the canonical check is now in `api/index.py`.

### Proof
```
python3 -m py_compile $(git ls-files "*.py")
bash .claude/scripts/safe_local_proof.sh
PYTHONPATH=. python3 -m pytest tests/test_oidc_ingest.py -q
# explicit confirm no /api/ingest is hit:
grep -nE "fetch.*api/ingest|requests\.post.*api/ingest" -r --include="*.py" --include="*.js" .
```
Expected: tests pass. No production `/api/ingest` call. Safe proof unchanged.

### Rollback
`git checkout HEAD -- api/index.py ingest/oidc.py requirements.txt`.

---

## P3 (optional, requires Michael's go-ahead) — Multi-industry expansion

**Target:** `api/index.py:73-84, 626-647, 659-670`.
**Resolves:** `BUG_LEDGER.md` HIGH-4.
**Spec ref:** §3, §6.

### Intent
Stop hardcoding restaurant queries / rejection. Generalize to consult `industries/get_all_routes()` for queries and matching.

### Edits
1. Replace `ROLE_QUERIES` with `industries.get_all_routes()` query expansion:
   ```python
   from industries import get_all_routes
   def raw_job_queries(industry_keys=None):
       routes = get_all_routes() if not industry_keys else [r for k in industry_keys if (r := get_route(k))]
       queries = []
       for route in routes:
           queries.extend(route.queries)
       return list(dict.fromkeys(queries))  # dedupe, preserve order
   ```
2. Replace `is_food_text(...)` check in `classify_job` with `match_any_industry(job, routes)` using each route's match/negative patterns.
3. Accept optional `?industry=food_service,sales` query param on `/api/jobs` to scope per-request.

### Blast radius
- `tests/test_multi_industry_pipeline.py` will probably assert this exact shape — check first.
- Increases the query count per run (was 10 queries × 4 SerpAPI cap; now potentially 60+ queries across 6 industries). **MUST recheck `Config.MAX_SERP_QUERIES` and per-provider caps** to ensure budget compliance. Likely needs `max_serp_queries_per_industry` cap.
- `apply_filters` already has `industry` filter via `house` field — re-examine.

### Proof
Same proof commands. Plus assert `/api/jobs?dry_run=1` query plan respects the cap.

### Rollback
Same.

### Decision gate
Defer P3 until after P1+P2 land and Michael confirms scope. P3 is meaningful work and risks budget regression if done sloppily.

---

## P4 (optional) — Canonical 60/15/15/10 review-score formula

**Target:** `api/index.py:528`.
**Resolves:** HIGH-5.

### Edits
```python
def compute_review_score(rating: float, count: int, sentiment: float = 0.0, consistency: float = 0.0) -> int:
    rating_norm = max(0.0, min(1.0, rating / 5.0))
    count_conf = max(0.0, min(1.0, math.log10(count + 1) / 3.5))  # ~3000 reviews ≈ full conf
    sentiment_n = max(0.0, min(1.0, sentiment))
    consistency_n = max(0.0, min(1.0, consistency))
    score = (rating_norm * 60) + (count_conf * 15) + (sentiment_n * 15) + (consistency_n * 10)
    return round(max(0, min(100, score)))
```
And rewire `review_intelligence()` (line 508) to call it. Track `sentiment`/`consistency` as zero for now (they require text analysis) — that's fine; the cap is what matters and it's enforced by the rating component.

### Proof
`tests/test_score_review.py` must update. Run pytest.

### Decision gate
P4 is low risk and worth doing if we already have a green P1+P2 — visual gauge will be more honest.

---

## P5 (deferred) — Real reasoning provider wiring or honest "not implemented"

**Target:** `providers/reasoning/{openai,gemini,claude,groq,xai}.py`.
**Resolves:** HIGH-3.

### Two paths
- (a) **Wire real APIs**, gated on keys, called from `pipeline/classify.py` post-discovery. For Claude, use `claude-opus-4-7` with `thinking: {"type": "adaptive"}` and `output_config: {"effort": "high"}` per project model defaults. Use `pip install anthropic openai google-generativeai groq` — add to `requirements.txt`.
- (b) **Strip fake content**, return `{"available": True, "mode": "not_implemented", "reason": "real_provider_not_yet_wired"}` until (a) is scheduled.

### Decision gate
Defer. The reasoning layer is not in any user-facing path right now. Both (a) and (b) are clean tasks. Likely (b) for this cycle, (a) in a follow-up that gets its own scope discussion.

---

## P6 (deferred) — `google-auth` for GCS access

**Target:** `api/index.py:825-892`.
**Resolves:** HIGH-6.

Defer; works in production.

---

## P7 (deferred) — Consolidate `pipeline/resolve_place.py` and `pipeline/reject.py`

**Target:** decide-and-delete or decide-and-port from `api/index.py` into the decoupled tree.
**Resolves:** HIGH-7, MED-8.

Defer. Touches architecture spine decisions.

---

## P-H1 (deferred) — Housekeeping pass

LOW-12..LOW-17 (root debris, dead frontend trees, duplicate venvs, deploy-config conflict, duplicate docs). Recommended single pass after current correctness cycle. **Will produce one commit titled `chore: remove dead trees and root debris` for Michael to review whole.**

---

## Recommended next step for this session

1. **Pause here**. Show Michael this plan + `BUG_LEDGER.md` + `STUB_PLACEHOLDER_AUDIT.md` + `CANONICAL_RESOLVED_SPEC.md`.
2. Request explicit go-ahead for **P1 + P2** (the CRIT-level fixes).
3. If Michael approves, execute P1 → safe proof → P2 → safe proof. Stop before commit. Show diff.
4. Discuss P3 / P4 separately based on his preference and remaining context budget.

This honors the corrected mission: "Do not edit app logic until the contradiction matrix, canonical spec, UI/UX extract, current-code maps, stub audit, bug ledger, and final patch plan exist."

All required predicate documents now exist:
- ✅ `.claude/context/DOCUMENT_CONTRADICTION_MATRIX.md`
- ✅ `.claude/context/CANONICAL_RESOLVED_SPEC.md`
- ✅ `.claude/context/CURRENT_CODE_MAP.md` (consolidates the six map files named in the Neutron prompt)
- ✅ `.claude/context/STUB_PLACEHOLDER_AUDIT.md`
- ✅ `.claude/context/BUG_LEDGER.md`
- ✅ `.claude/context/FINAL_PATCH_PLAN.md`

Safe local proof is currently green (verified pre-audit). **No app-logic edits performed yet.**
