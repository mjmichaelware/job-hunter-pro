#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="ai-job-agent-498702"
REGION="us-central1"
SERVICE="job-hunter-pro"

fail(){ echo "FAIL: $1"; exit 1; }

echo "=== S10 LIVE DATA CONTRACT FIX ==="
echo "PWD=$(pwd)"
[ -f app.py ] || fail "not in repo root"
[ -f web/static/js/render_jobs.js ] || fail "missing render_jobs.js"
[ -f web/static/js/render_opportunities.js ] || fail "missing render_opportunities.js"
[ -f web/static/js/render_overview.js ] || fail "missing render_overview.js"

echo
echo "=== 1) Pre-patch inspection ==="
grep -Rni "async function loadJobs\|dry_run=1\|dry_run: 0\|renderJobsList\|data\.jobs\|data\.opportunities\|function normalize\|opportunities-container\|overview-accepted-count\|overview-opp-count\|overview-budget-burn" \
  web/static/js/render_jobs.js web/static/js/render_opportunities.js web/static/js/render_overview.js web/static/js/state.js web/static/js/api.js || true

echo
echo "=== 2) Backup frontend files outside git path ==="
mkdir -p .repair_backups
TS="$(date +%Y%m%d_%H%M%S)"
cp web/static/js/render_jobs.js ".repair_backups/render_jobs.js.s10_contract.${TS}"
cp web/static/js/render_opportunities.js ".repair_backups/render_opportunities.js.s10_contract.${TS}"
cp web/static/js/render_overview.js ".repair_backups/render_overview.js.s10_contract.${TS}"

echo
echo "=== 3) Write payload-compatible render_jobs.js ==="
cat > web/static/js/render_jobs.js <<'JS'
function normalizeJobsPayload(payload) {
  if (!payload || typeof payload !== 'object') return [];
  if (Array.isArray(payload.jobs)) return payload.jobs;
  if (Array.isArray(payload.data)) return payload.data;
  if (payload.data && Array.isArray(payload.data.jobs)) return payload.data.jobs;
  if (Array.isArray(payload.results)) return payload.results;
  return [];
}

function pickJobField(job, keys, fallback = '') {
  for (const key of keys) {
    const value = job?.[key];
    if (value !== undefined && value !== null && value !== '') return value;
  }
  return fallback;
}

function jobNumber(value, fallback = null) {
  if (value === undefined || value === null || value === '') return fallback;
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

async function loadJobs(options = {}) {
  const { live = false } = options || {};
  const container = document.getElementById('jobs-container');
  if (!container) return;

  container.innerHTML = live
    ? '<div class="chart-fallback">Running live discovery. This may use discovery provider budget.</div>'
    : '<div class="chart-fallback">Checking safe dry-run status. Opening this dashboard does not run live discovery.</div>';

  const url = live ? API_URLS.jobs : `${API_URLS.jobs}?dry_run=1`;
  const data = await safeFetch(url);

  AppState.cachedData.jobs = data;
  renderJobsList(data, { live });
}

function renderJobsList(data, options = {}) {
  const { live = false } = options || {};
  const container = document.getElementById('jobs-container');
  if (!container) return;

  const jobs = normalizeJobsPayload(data);

  if (!jobs.length) {
    if (data?.dry_run) {
      container.innerHTML = `
        <div class="chart-fallback">
          <strong>Live jobs are not loaded yet.</strong><br>
          ${escapeHtml(data.message || 'Dry run completed without spending discovery provider budget.')}<br>
          Use <strong>Run Live Discovery</strong> when ready to spend provider budget.
        </div>`;
      return;
    }

    container.innerHTML = live
      ? '<div class="chart-fallback">Live discovery returned no accepted jobs for the current filters.</div>'
      : '<div class="chart-fallback">No live jobs loaded. Run live discovery when ready to spend provider budget.</div>';
    return;
  }

  let filtered = jobs.filter((job) => {
    const industry = pickJobField(job, ['industry', 'industry_key'], '');
    const radius = jobNumber(pickJobField(job, ['haversine_radius_miles', 'radius_miles', 'distance_miles'], null), null);
    const match = jobNumber(pickJobField(job, ['match_score', 'score', 'resonance_score'], null), null);

    if (AppState.filters?.industry && industry && industry !== AppState.filters.industry) return false;
    if (radius !== null && AppState.filters?.radius && radius > Number(AppState.filters.radius)) return false;
    if (match !== null && AppState.filters?.matchScore && match < Number(AppState.filters.matchScore)) return false;
    return true;
  });

  if (!filtered.length) {
    container.innerHTML = '<div class="chart-fallback">No live jobs match current filters. Adjust filters or run a broader discovery.</div>';
    return;
  }

  container.innerHTML = filtered.map((job) => {
    const title = escapeHtml(pickJobField(job, ['title', 'job_title', 'name'], 'Untitled role'));
    const company = escapeHtml(pickJobField(job, ['company', 'company_name', 'employer', 'place_name'], 'Company unavailable'));
    const address = escapeHtml(pickJobField(job, ['normalized_address', 'address', 'location', 'detected_location'], 'Address unresolved'));
    const source = escapeHtml(pickJobField(job, ['source', 'provider', 'source_provider_id'], 'source unavailable'));
    const salary = escapeHtml(pickJobField(job, ['salary', 'salary_hint', 'pay', 'compensation'], 'Salary not listed'));

    const match = jobNumber(pickJobField(job, ['match_score', 'score', 'resonance_score'], null), null);
    const review = jobNumber(pickJobField(job, ['review_score', 'review_heuristic_score'], null), null);
    const rating = jobNumber(pickJobField(job, ['rating', 'place_rating'], null), null);
    const reviews = jobNumber(pickJobField(job, ['review_count', 'place_review_count'], null), null);
    const transitSeconds = jobNumber(pickJobField(job, ['commute_matrix_seconds', 'transit_seconds', 'commute_seconds'], null), null);
    const radius = jobNumber(pickJobField(job, ['haversine_radius_miles', 'radius_miles', 'distance_miles'], null), null);
    const tags = [
      pickJobField(job, ['role_family'], ''),
      pickJobField(job, ['industry'], ''),
      source ? `source: ${source}` : ''
    ].filter(Boolean).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('');

    const commuteCopy = transitSeconds !== null
      ? `${Math.round(transitSeconds / 60)} min transit`
      : 'Transit unavailable';

    const distanceCopy = radius !== null
      ? `${radius.toFixed(1)} mi`
      : 'Distance unavailable';

    const scoreCopy = match !== null
      ? `${Math.round(match)}% match`
      : 'Match unavailable';

    const reviewCopy = [
      rating !== null ? `${rating.toFixed(1)}★` : null,
      reviews !== null ? `${reviews} reviews` : null,
      review !== null ? `Review score ${Math.round(review)}` : null
    ].filter(Boolean).join(' · ') || 'Review intelligence unavailable';

    return `
      <article class="job-card card" style="margin-bottom: var(--space-md);">
        <div style="display:flex; justify-content:space-between; gap:var(--space-md); align-items:flex-start;">
          <div>
            <h3>${title}</h3>
            <p class="muted">${company}</p>
            <p class="muted">${address} · ${distanceCopy} · ${commuteCopy}</p>
          </div>
          <span class="badge badge-safe">${escapeHtml(scoreCopy)}</span>
        </div>
        <p style="margin-top:var(--space-sm);">${reviewCopy}</p>
        <p style="margin-top:var(--space-sm); color:var(--success); font-weight:700;">${salary}</p>
        <div style="margin-top:var(--space-sm); display:flex; flex-wrap:wrap; gap:6px;">${tags}</div>
      </article>`;
  }).join('');
}
JS

echo
echo "=== 4) Write payload-compatible render_opportunities.js ==="
cat > web/static/js/render_opportunities.js <<'JS'
function normalizeOpportunitiesPayload(payload) {
  if (!payload || typeof payload !== 'object') return [];
  if (Array.isArray(payload.opportunities)) return payload.opportunities;
  if (Array.isArray(payload.data)) return payload.data;
  if (payload.data && Array.isArray(payload.data.opportunities)) return payload.data.opportunities;
  if (Array.isArray(payload.results)) return payload.results;
  return [];
}

async function loadOpportunities() {
  const container = document.getElementById('opportunities-container');
  if (!container) return;

  container.innerHTML = '<div class="chart-fallback">Loading cached Google Places opportunities...</div>';

  const data = await safeFetch(API_URLS.opportunities);
  AppState.cachedData.opportunities = data;
  renderOpportunitiesList(data);
}

function renderOpportunitiesList(data) {
  const container = document.getElementById('opportunities-container');
  if (!container) return;

  const opportunities = normalizeOpportunitiesPayload(data);

  if (!opportunities.length) {
    container.innerHTML = '<div class="chart-fallback">No opportunities loaded or matched current filters.</div>';
    return;
  }

  let filtered = opportunities.filter((opp) => {
    const industry = opp?.industry || opp?.industry_key || '';
    if (AppState.filters?.industry && industry && industry !== AppState.filters.industry) return false;
    return true;
  });

  if (!filtered.length) {
    container.innerHTML = '<div class="chart-fallback">No opportunities match current filters.</div>';
    return;
  }

  container.innerHTML = `
    <div class="notice">Loaded ${filtered.length} nearby restaurant opportunities.</div>
    ${filtered.map((opp) => {
      const name = escapeHtml(opp?.name || opp?.business_name || opp?.company || 'Unnamed opportunity');
      const address = escapeHtml(opp?.address || opp?.formatted_address || opp?.vicinity || 'Address unavailable');
      const rating = opp?.rating ?? opp?.place_rating ?? null;
      const reviewCount = opp?.review_count ?? opp?.user_ratings_total ?? null;
      const category = escapeHtml(opp?.category || opp?.primary_type || opp?.type || 'local opportunity');
      const ratingCopy = rating !== null && rating !== undefined ? `${rating}★` : 'Rating unavailable';
      const reviewCopy = reviewCount !== null && reviewCount !== undefined ? `${reviewCount} reviews` : 'review count unavailable';

      return `
        <article class="card" style="margin-bottom:var(--space-sm);">
          <div style="display:flex; justify-content:space-between; gap:var(--space-md); align-items:flex-start;">
            <div>
              <h3>${name}</h3>
              <p class="muted">${address}</p>
              <p class="muted">${category}</p>
            </div>
            <span class="badge badge-cached">${escapeHtml(ratingCopy)}</span>
          </div>
          <p style="margin-top:var(--space-sm);">${escapeHtml(reviewCopy)}</p>
        </article>`;
    }).join('')}`;
}
JS

echo
echo "=== 5) Patch overview counters to understand real payload keys ==="
python3 - <<'PY'
from pathlib import Path

p = Path("web/static/js/render_overview.js")
text = p.read_text(encoding="utf-8")

if "function countArrayPayload" not in text:
    helper = r'''
function countArrayPayload(payload, keys) {
  if (!payload || typeof payload !== 'object') return 0;
  for (const key of keys) {
    const value = payload[key];
    if (Array.isArray(value)) return value.length;
    if (typeof value === 'number') return value;
  }
  if (payload.data) {
    if (Array.isArray(payload.data)) return payload.data.length;
    if (typeof payload.data === 'object') {
      for (const key of keys) {
        const value = payload.data[key];
        if (Array.isArray(value)) return value.length;
        if (typeof value === 'number') return value;
      }
    }
  }
  return 0;
}

function pickUsageLeft(usage) {
  if (!usage || typeof usage !== 'object') return null;
  if (usage.total_searches_left !== undefined) return usage.total_searches_left;
  if (usage.serpapi?.total_searches_left !== undefined) return usage.serpapi.total_searches_left;
  if (usage.serpapi?.searches_left !== undefined) return usage.serpapi.searches_left;
  if (usage.serpapi?.remaining !== undefined) return usage.serpapi.remaining;
  return null;
}

'''
    text = helper + "\n" + text

text = text.replace(
    "acceptedCount.textContent = jobs?.jobs?.length ?? '—';",
    "acceptedCount.textContent = countArrayPayload(jobs, ['jobs', 'count', 'job_count']) || '—';"
)
text = text.replace(
    "oppCount.textContent = opportunities?.opportunities?.length ?? '—';",
    "oppCount.textContent = countArrayPayload(opportunities, ['opportunities', 'data', 'count']) || '—';"
)
text = text.replace(
    "batchCount.textContent = history?.batches?.length ?? '—';",
    "batchCount.textContent = countArrayPayload(history, ['batches', 'history', 'batch_count']) || '—';"
)

# If budgetBurn had old direct fields, add a conservative fallback without overfitting.
if "pickUsageLeft(usage)" not in text.split("async function loadOverview", 1)[-1]:
    text = text.replace(
        "budgetBurn.textContent = usage?.serpapi?.total_searches_left ?? usage?.total_searches_left ?? '—';",
        "budgetBurn.textContent = pickUsageLeft(usage) ?? '—';"
    )

p.write_text(text, encoding="utf-8")
PY

echo
echo "=== 6) Post-patch inspection ==="
grep -Rni "async function loadJobs\|live = false\|dry_run=1\|normalizeJobsPayload\|normalizeOpportunitiesPayload\|countArrayPayload\|pickUsageLeft\|API_URLS.jobs" \
  web/static/js/render_jobs.js web/static/js/render_opportunities.js web/static/js/render_overview.js web/static/js/state.js web/static/js/api.js || true

echo
echo "=== 7) Compile Python ==="
python3 -m py_compile $(git ls-files '*.py')

echo
echo "=== 8) Local Flask safe proof, no live discovery ==="
python3 - <<'PY'
from app import app

c = app.test_client()

for path in ["/", "/api/health", "/api/usage", "/api/jobs?dry_run=1", "/api/opportunities", "/api/history"]:
    r = c.get(path)
    print(path, r.status_code, r.content_type)
    assert r.status_code == 200

root = c.get("/").get_data(as_text=True)
assert "prepare-discovery-btn" in root
assert "jobs-container" in root
assert "opportunities-container" in root

jobs_js = c.get("/static/js/render_jobs.js").get_data(as_text=True)
assert "async function loadJobs(options = {})" in jobs_js
assert "live ? API_URLS.jobs" in jobs_js
assert "?dry_run=1" in jobs_js

opps_js = c.get("/static/js/render_opportunities.js").get_data(as_text=True)
assert "normalizeOpportunitiesPayload" in opps_js
assert "Array.isArray(payload.data)" in opps_js

print("PASS: frontend now distinguishes safe dry-run from explicit live discovery and reads opportunities data[].")
PY

echo
echo "=== 9) Diff proof ==="
git diff -- web/static/js/render_jobs.js web/static/js/render_opportunities.js web/static/js/render_overview.js
git diff --check

echo
echo "=== 10) Commit and push ==="
git add web/static/js/render_jobs.js web/static/js/render_opportunities.js web/static/js/render_overview.js
git commit -m "S10 restore live data frontend contract"
git push origin main

echo
echo "=== 11) Wait for Cloud Build trigger ==="
sleep 120

echo
echo "=== 12) Verify live service ==="
SERVICE_URL="$(gcloud run services describe "$SERVICE" --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')"
echo "SERVICE_URL=$SERVICE_URL"

gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format="table(status.url,status.latestReadyRevisionName,status.traffic[0].revisionName,status.traffic[0].percent)"

echo
echo "=== 13) Live health ==="
curl -fsS "$SERVICE_URL/api/health"
echo

echo
echo "=== 14) Live JS proof ==="
echo "--- render_jobs.js ---"
curl -fsS "$SERVICE_URL/static/js/render_jobs.js?v=$(date +%s)" | grep -E "async function loadJobs|live = false|normalizeJobsPayload|live \? API_URLS.jobs|\?dry_run=1" || true

echo
echo "--- render_opportunities.js ---"
curl -fsS "$SERVICE_URL/static/js/render_opportunities.js?v=$(date +%s)" | grep -E "normalizeOpportunitiesPayload|Array.isArray\(payload.data\)|Loaded .* nearby restaurant opportunities" || true

echo
echo "OPEN:"
echo "$SERVICE_URL/?v=live-contract-$(date +%s)"
echo
echo "DONE. Opening the app is still safe. Live jobs load only after pressing Run Live Discovery."
