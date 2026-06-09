# Bug Ledger — Job Hunter Pro

Only confirmed defects: code citation or safe-proof evidence required. Each entry has ID, severity, canonical-spec reference, evidence, current behavior, expected behavior, and recommendation. The patch plan (`FINAL_PATCH_PLAN.md`) acts on this ledger.

Severity scale: **CRIT** (data-truth or security regression actively shipping), **HIGH** (canonical-spec violation that materially affects the user), **MED** (visible defect with a workaround), **LOW** (housekeeping / quality).

---

## CRIT-1. Rejection gate silently disabled — all jobs accepted

**Spec ref:** Canonical §6 (live jobs visibility), §1.8 (no fake data — `rejected_count` is now structurally lying), §14 acceptance criteria.

**Evidence:**
```
api/index.py:626  def rejection_reasons(job: Dict[str, Any]) -> List[str]:
api/index.py:627      reasons = []
api/index.py:628-647  # builds reasons: not_food_service, no_exact_restaurant_address_resolved,
                      #                radius_unavailable, outside_radius_*mi,
                      #                transit_unavailable, transit_too_long_*min
api/index.py:648      return []   # <-- discards `reasons`, always empty
```
Call site (`api/index.py:721-742`):
```
reasons = rejection_reasons(job)
if reasons:                # always False
    rejected.append(...)   # never executes
else:
    ... accepted.append(job)
```

**Current behavior:** Every raw job from `fetch_provider_raw_jobs` becomes `accepted`. `rejected_count` is always 0, `rejection_summary` is always `{}`, `rejected` array is always empty. Non-food jobs, jobs with unresolved place, jobs outside radius, and jobs with unknown transit all appear in the user's "accepted" list with no signal of their issue.

**Expected behavior per canonical §6:**
- Jobs missing place / radius / transit resolution → keep visible, attach `resolution_flags: ["address_unresolved" | "radius_unknown" | "transit_unknown"]` and set `needs_resolution: true`. Bucket into `unresolved`, not `rejected`.
- Jobs with genuine disqualifiers (`not_in_industry`, `ambiguous_place_resolution`, `outside_radius_X`, `transit_too_long_X`, `duplicate`, `missing_source_url`, `provider_error`, `budget_guard`) → reject with reason.
- `/api/jobs` response shape grows to include `unresolved` and per-bucket counts.

**Recommendation:** Track in patch plan as P1. Highest priority.

---

## CRIT-2. `verify_oidc()` does not actually verify OIDC

**Spec ref:** Canonical §1.3 (`/api/ingest` protected by Cloud Scheduler OIDC), §11.

**Evidence:**
```
api/index.py:1183  def verify_oidc():
api/index.py:1184      auth_header = request.headers.get("Authorization")
api/index.py:1185      if not auth_header or not auth_header.startswith("Bearer "):
api/index.py:1186          logger.warning("Missing or malformed Authorization header")
api/index.py:1187          return False
api/index.py:1188      # For S12-Omega proof, we assume Cloud Run/App Engine is verifying the token signature
api/index.py:1189      # and we only check if the header exists. In a full S12, we'd use google-auth.
api/index.py:1190      return True
```
And earlier in `app.py:130-138`, the same Bearer-prefix-only check is applied before the proxy.

**Current behavior:** Anyone who sends `Authorization: Bearer x` to `/api/ingest` is admitted. JWT signature, audience, issuer, and email are NOT validated. Cloud Run does NOT auto-verify OIDC on `--allow-unauthenticated` services — this assumption is wrong.

**Expected behavior per canonical §11:** `verify_oidc` must:
1. Extract token from `Authorization: Bearer <token>`.
2. Verify signature via Google's JWKS (`https://www.googleapis.com/oauth2/v3/certs`).
3. Validate `aud` claim equals the Cloud Run service URL.
4. Validate `email` claim equals `job-hunter-scheduler@ai-job-agent-498702.iam.gserviceaccount.com`.
5. Validate `exp` is not past.

The decoupled `ingest/oidc.py` exists; it likely already does this (not yet read in full but its presence in scope is correct). Route `/api/ingest` should call it.

**Recommendation:** Track in patch plan as P2. Security regression; fix together with CRIT-1.

---

## HIGH-3. Reasoning providers return fabricated enrichment data

**Spec ref:** Canonical §1.8 (no fake data), §4.2 (LLM reasoning providers).

**Evidence:**
```
providers/reasoning/openai.py:42-50
    def enrich(self, text_content):
        if not self.is_available(): return {"provider": ..., "available": False}
        return {
            "provider": "openai",
            "mode": "enrich",
            "confidence": 0.9,
            "evidence_required": True,
            "enrichment": {"summary": "Enriched content placeholder", "tags": ["job", "tech"]},
            ...
        }
```
Same pattern in `providers/reasoning/claude.py:40-48` ("Claude enriched summary"). Likely also in `gemini.py`, `groq.py`, `xai.py` (`reasoning/base.py` is just `"""S0 scaffold placeholder."""`).

**Current behavior:** When API key is present, `enrich()` reports `confidence: 0.9, evidence_required: True` with a hardcoded summary — that is, the *shape* of a real LLM response with FAKE content. This is precisely the "no fake enrichment" violation called out by Doc 5 ("AI_found_these_jobs_without_evidence", "magic_AI").

**However:** these providers are NOT wired into the active live-jobs pipeline. `api/index.py` uses purely deterministic enrichment (`review_intelligence`, `match_score`, `tags_for_text`). The fake enrichment is only reachable via `pipeline/classify.py` or `pipeline/run.py`, neither of which is in the active path.

**Expected behavior:** Either (a) implement real API calls when keys are present, or (b) clearly mark as `available=False, mode="not_implemented"` and return no fake fields.

**Recommendation:** Track in patch plan as P5 (post-CRIT fixes). Either ship real implementations (Claude using `claude-opus-4-7` adaptive thinking per project defaults) or strip fake content and mark as unimplemented.

---

## HIGH-4. Live-jobs pipeline ignores 6-industry expansion

**Spec ref:** Canonical §3 (6 industries), §6 (multi-industry classification expected).

**Evidence:**
```
api/index.py:73-84   ROLE_QUERIES = ["restaurant server jobs near 84115...", ...] # 10 entries, all restaurant
api/index.py:659-670 def raw_job_queries():
                         queries = list(ROLE_QUERIES)
                         for restaurant in nearby_opportunities_cached(...)[:8]: ...
                         # injects ' "<name>" restaurant jobs ' queries
api/index.py:626-647 def rejection_reasons(job):
                         if not is_food_text(food_text):
                             reasons.append("not_food_service")  # food-only gate
```
`industries/` has 6 routes defined; `industries/__init__.py` exports `get_all_routes()`; `industries/<name>.py` each declare `queries`, `match`, `negative`, `role_families`. None of these are consulted from the live path.

**Current behavior:** Live discovery only searches for restaurant jobs. A user filtering by `industry=sales` in the UI sees no relevant results because the query plan never asked any provider for sales jobs in the first place.

**Expected behavior:** `raw_job_queries()` consults `industries.get_all_routes()` (or the active industry filter) and emits queries for each enabled industry. Rejection's "not_in_industry" check uses `industries/<key>.match` patterns instead of `is_food_text()`.

**Recommendation:** Track in patch plan as P3. Fold together with CRIT-1 (rejection logic refactor).

---

## HIGH-5. Review-score formula does not match canonical 60/15/15/10

**Spec ref:** Canonical §9 (UI review-score gauge geometry-capped at rating·60%), §14 acceptance criteria.

**Evidence:**
```
api/index.py:528
    score = round(min(100, max(0, (rating_float / 5) * 90 + min(10, math.log10(count_int + 1) * 4)))) if rating_float else 50
```

**Current behavior:** With `rating=5.0` and `count=10`: `5/5*90 + log10(11)*4 = 90 + 4.17 = 94`. With `rating=3.7` and `count=10000`: `3.7/5*90 + log10(10001)*4 = 66.6 + 16 → clamped 10 = 76.6 → 77`. This still over-rewards volume. The historical defect (IHOP 3.7 → 100) is partly mitigated by the cap at `90 + 10 = 100` for 5-star, but 3.7-star with high volume still gets 77 — Doc 1 said this should be capped *lower* by the rating.

**Expected behavior per canonical §14 / Doc 1:**
```
review_score = rating_norm * 60        # max 60 if rating=5.0
             + count_confidence * 15   # max 15
             + sentiment_score * 15    # max 15
             + consistency_score * 10  # max 10
# Total capped at 100; geometry guarantees that low rating → low score.
```
A 3.7-star place is now capped at `0.74·60 + 15 + 15 + 10 = 84.4` if everything else is perfect, vs. the canonical intent of using the multiplicative cap so a low rating cannot reach perfect.

**Recommendation:** Track in patch plan as P4. Replace the formula and update tests in `tests/test_score_review.py`.

---

## HIGH-6. Live ingest writes GCS via raw HTTP + metadata token

**Spec ref:** Canonical §11 (security — use `google-auth AuthorizedSession`), Doc 1 §"Security/Deployment Requirements".

**Evidence:**
```
api/index.py:825  def metadata_access_token():
                      res = session.get(
                          "http://metadata.google.internal/.../service-accounts/default/token",
                          headers={"Metadata-Flavor": "Google"}, timeout=5)
                      return res.json().get("access_token", "")
api/index.py:843  def gcs_upload_json(...):
                      session.post(
                          f"https://storage.googleapis.com/upload/storage/v1/b/{Config.BATCH_BUCKET}/o",
                          headers=gcs_headers(),  # = {"Authorization": f"Bearer {metadata_access_token()}", ...}
                          ...)
```
`google-cloud-storage==2.14.0` and `google-cloud-firestore==2.14.0` are in `requirements.txt` but unused.

**Current behavior:** Tokens are fetched fresh on every call (no caching, no refresh) and short-circuit on metadata failure. Code is brittle and harder to test.

**Expected behavior:** Use `google.cloud.storage.Client()` for GCS, or migrate batches to Firestore via the decoupled `store/firestore_client.py` per spec §10.

**Recommendation:** Track in patch plan as P6 (low urgency — works in production). Pair with `store/` migration when scheduled.

---

## HIGH-7. `pipeline/resolve_place.py` is an 8-line stub that returns fake data

**Spec ref:** Canonical §1.8 (no fake data).

**Evidence:**
```
pipeline/resolve_place.py:
def resolve_place(job: dict) -> dict:
    loc = job.get("location", "").strip().lower()
    if not loc:
        job["resolved_place"] = None
    else:
        job["resolved_place"] = f"resolved_{loc}"
    return job
```

**Current behavior:** This module exists in the decoupled tree but is **not called by the live path** (`api/index.py` has its own real `resolve_place` at line 436). However, `pipeline/run.py` (the decoupled orchestrator) likely imports this stub.

**Expected behavior:** Either:
- Delete the file (legacy unused) and ensure `pipeline/run.py` (and anything else) doesn't import it.
- Or implement it properly by wrapping `geo/places_text.py` + `geo/geocode.py`.

**Recommendation:** Track in patch plan as P7. Decision: probably delete + leave the canonical resolve_place in `api/index.py` for now. Fold into the future "consolidate pipeline" effort.

---

## MED-8. `pipeline/reject.py` does not match canonical reasons list

**Spec ref:** Canonical §6.

**Evidence:**
```
pipeline/reject.py:
def reject_late(job):
    if job.get("industry") == "unknown":
        return {"reason": "not_mapped_to_industry", ...}
    if match_score < 40:
        return {"reason": "low_match_score", ...}
    return None
```
Missing all canonical reasons: `not_in_industry`, `ambiguous_place_resolution`, `duplicate`, `provider_error`, `budget_guard`, `missing_source_url`. Missing `resolution_flags` logic.

**Current behavior:** Unused (live path is `api/index.py:rejection_reasons`).

**Expected behavior:** Either bring up to spec or delete. Companion to HIGH-7.

**Recommendation:** Track in patch plan as P7 alongside HIGH-7.

---

## MED-9. Two storage layers — Firestore repos exist but unused

**Spec ref:** Canonical §10 (Firestore Native primary), §2.

**Evidence:** `store/firestore_client.py`, `store/jobs_repo.py`, `store/batches_repo.py`, `store/cache_repo.py`, etc., are present. `api/index.py` writes batches to GCS only. Active ingest never touches Firestore.

**Current behavior:** Decoupled storage layer is dormant. Batch history is in GCS JSON. Spec wants Firestore as primary.

**Expected behavior:** Migrate ingest to write Firestore via `store/batches_repo.py`. Keep GCS as legacy read fallback. Migration is non-trivial and may not be in the current patch cycle.

**Recommendation:** Defer to a follow-up cycle. Note in patch plan.

---

## MED-10. Dead frontend trees (`templates/`, `static/`, `public/`, top-level `index.html`)

**Spec ref:** Housekeeping; STUB_PLACEHOLDER_AUDIT §C.

**Evidence:** `app.py` mounts `web/` only. Other trees are not served by any active route.

**Current behavior:** Dead. Risk: someone edits the wrong tree.

**Recommendation:** Track in patch plan as housekeeping P-H1; defer until current-cycle fixes ship.

---

## MED-11. Dead modular `api/*.py` route files

**Spec ref:** Architecture spine §2; STUB_PLACEHOLDER_AUDIT §C5.

**Evidence:** `api/health.py`, `api/history.py`, `api/opportunities.py`, `api/research.py`, `api/usage.py`, `api/why_three.py` exist but are not imported by `api/__init__.py`. The proxy in `app.py` forwards these endpoints to `api/index.py`.

**Current behavior:** Two-truths setup. The modular files are dead duplicates of legacy `api/index.py` endpoints.

**Recommendation:** Either wire them (and stop proxying) or delete. Defer to follow-up cycle when the legacy `api/index.py` is decomposed.

---

## LOW-12 through LOW-17. Housekeeping items

| ID | Item | Source |
|---|---|---|
| LOW-12 | Top-level repair shell scripts (14 files) | STUB §D1 |
| LOW-13 | Top-level debug Python (3 files) | STUB §D2 |
| LOW-14 | Duplicate `venv/` virtualenv | STUB §D3 |
| LOW-15 | `.repair_backups/`, `.claude_backup_*` in repo | STUB §D4 |
| LOW-16 | Conflicting deploy configs (Dockerfile, Procfile, cloudbuild.yaml, vercel.json) | STUB §D6 |
| LOW-17 | Duplicate raw docs (`AI_JOB_AGENT_5.txt`, `AI_JOB_AGENT_6.txt`) | STUB §C7 |

Deferred to a housekeeping pass after the current correctness patch lands.

---

## Severity tally

| Severity | Count |
|---|---|
| CRIT | 2 |
| HIGH | 5 |
| MED | 4 |
| LOW | 6 |

The two CRIT items (CRIT-1 rejection-gate disabled, CRIT-2 OIDC not enforced) are the must-fix set for this patch cycle. HIGH-3..HIGH-7 are real but scoped; HIGH-4 (multi-industry) pairs naturally with the CRIT-1 fix.
