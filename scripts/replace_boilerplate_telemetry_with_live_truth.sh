#!/usr/bin/env bash

# Context Anchor for Subdirectory Migration
cd "$(dirname "$0")/.."
set -euo pipefail

PROJECT_ID="ai-job-agent-498702"
REGION="us-central1"
SERVICE="job-hunter-pro"

fail(){ echo "FAIL: $1"; exit 1; }

echo "=== S0: REPLACE BOILERPLATE TELEMETRY WITH LIVE TRUTH ==="
echo "PWD=$(pwd)"
[ -f app.py ] || fail "not in repo root"
[ -f web/templates/index.html ] || fail "missing web/templates/index.html"

echo
echo "=== S1: Inspect boilerplate telemetry strings ==="
grep -Rni "Shedding Registry\|Real-time Logs\|Pipeline reactor initialized\|Awaiting SSE\|Stream endpoint unavailable\|Rendering static telemetry readiness\|SSE DISCONNECTED\|telemetry readiness" \
  web/templates/index.html web/static/js web/static/css 2>/dev/null || true

echo
echo "=== S2: Create live truth telemetry module ==="
cat > web/static/js/live_truth_telemetry.js <<'JS'
(function () {
  function esc(value) {
    if (window.escapeHtml) return window.escapeHtml(value);
    return String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
  }

  function hideBoilerplateTelemetry() {
    const badText = [
      'Shedding Registry',
      'Real-time Logs',
      'Pipeline reactor initialized',
      'Awaiting SSE stream connection',
      'Stream endpoint unavailable',
      'Rendering static telemetry readiness',
      'SSE DISCONNECTED'
    ];

    const candidates = Array.from(document.querySelectorAll('section, article, .card, div'));
    for (const node of candidates) {
      const text = (node.textContent || '').trim();
      if (!text) continue;

      const isBoilerplate = badText.some(token => text.includes(token));
      if (!isBoilerplate) continue;

      const card = node.closest('.card') || node.closest('section') || node;
      if (card && card.id !== 'live-truth-telemetry') {
        card.style.display = 'none';
        card.setAttribute('data-hidden-reason', 'replaced-by-live-truth-telemetry');
      }
    }
  }

  function ensurePanel() {
    let panel = document.getElementById('live-truth-telemetry');
    if (panel) return panel;

    const overview =
      document.getElementById('tab-overview') ||
      document.querySelector('main') ||
      document.body;

    panel = document.createElement('section');
    panel.id = 'live-truth-telemetry';
    panel.className = 'card';
    panel.style.marginBottom = 'var(--space-lg)';
    panel.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:var(--space-md);align-items:flex-start;flex-wrap:wrap;">
        <div>
          <h3>Live Pipeline Truth</h3>
          <p class="muted">Real telemetry from safe endpoints and the latest explicit live discovery run.</p>
        </div>
        <span class="badge badge-safe">NO FAKE SSE</span>
      </div>
      <div id="live-truth-metrics" class="grid-overview" style="margin-top:var(--space-md);"></div>
      <div id="live-truth-provider-breakdown" style="margin-top:var(--space-md);"></div>
      <div id="live-truth-rejection-summary" style="margin-top:var(--space-md);"></div>
    `;

    const firstCard = overview.querySelector('.card');
    if (firstCard && firstCard.parentNode) {
      firstCard.parentNode.insertBefore(panel, firstCard);
    } else {
      overview.prepend(panel);
    }

    return panel;
  }

  function metric(label, value, klass) {
    return `
      <div class="card">
        <div class="metric-label">${esc(label)}</div>
        <div class="metric-num">${esc(value)}</div>
        <span class="badge ${klass || 'badge-cached'}">${esc(klass ? klass.replace('badge-', '') : 'live')}</span>
      </div>`;
  }

  async function getJson(path) {
    try {
      const res = await fetch(path, { cache: 'no-store' });
      const json = await res.json().catch(() => null);
      return { ok: res.ok, status: res.status, json };
    } catch (err) {
      return { ok: false, status: 0, json: { error: String(err) } };
    }
  }

  function latestJobsPayload() {
    const cached = window.AppState?.cachedData?.jobs;
    if (cached && typeof cached === 'object') return cached;
    return null;
  }

  function providerBreakdownHtml(payload) {
    const breakdown = payload?.provider_breakdown || {};
    const keys = Object.keys(breakdown);

    if (!keys.length) {
      return `
        <div class="chart-fallback">
          Provider fan-out appears after pressing <strong>Run Live Discovery</strong>.
        </div>`;
    }

    return `
      <h4>Provider Fan-Out</h4>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:var(--space-sm);">
        ${keys.map(key => {
          const info = breakdown[key] || {};
          const raw = info.raw_count ?? 0;
          const attempted = info.queries_attempted ?? 0;
          const status = info.status || (info.available ? 'ok' : 'dormant');
          const klass = raw > 0 ? 'badge-safe' : (info.available ? 'badge-cached' : 'badge-budget-guarded');
          return `<span class="badge ${klass}">${esc(key)}: ${esc(raw)} raw / ${esc(attempted)} q / ${esc(status)}</span>`;
        }).join('')}
      </div>`;
  }

  function rejectionSummaryHtml(payload) {
    const summary = payload?.rejection_summary || {};
    const entries = Object.entries(summary);

    if (!entries.length) {
      return `
        <div class="chart-fallback">
          No rejection summary is available yet. Run live discovery to populate real rejection telemetry.
        </div>`;
    }

    return `
      <h4>Resolution / Rejection Reasons</h4>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:var(--space-sm);">
        ${entries.map(([reason, count]) => `<span class="badge badge-budget-guarded">${esc(reason)} × ${esc(count)}</span>`).join('')}
      </div>`;
  }

  async function renderLiveTruthTelemetry() {
    hideBoilerplateTelemetry();
    ensurePanel();

    const metrics = document.getElementById('live-truth-metrics');
    const providers = document.getElementById('live-truth-provider-breakdown');
    const rejections = document.getElementById('live-truth-rejection-summary');

    const health = await getJson('/api/health');
    const usage = await getJson('/api/usage');
    const dryRun = await getJson('/api/jobs?dry_run=1');

    const payload = latestJobsPayload();
    const hasLivePayload = payload && payload.status === 'success' && !payload.dry_run;

    const serpLeft =
      usage.json?.serpapi?.total_searches_left ??
      usage.json?.serpapi?.searches_left ??
      usage.json?.serpapi?.remaining ??
      '—';

    const rawCount = hasLivePayload ? (payload.raw_count ?? '—') : 'not run';
    const acceptedCount = hasLivePayload ? (payload.count ?? payload.data?.length ?? 0) : 'not run';
    const unresolvedCount = hasLivePayload ? (payload.rejected_count ?? payload.rejected?.length ?? 0) : 'not run';
    const queryCount = hasLivePayload ? (payload.query_count ?? '—') : (dryRun.json?.max_serp_queries ?? 'ready');

    if (metrics) {
      metrics.innerHTML = [
        metric('Health', health.json?.status || health.status || 'unknown', health.ok ? 'badge-safe' : 'badge-budget-guarded'),
        metric('SerpAPI Left', serpLeft, 'badge-cached'),
        metric('Raw Candidates', rawCount, hasLivePayload ? 'badge-safe' : 'badge-cached'),
        metric('Accepted', acceptedCount, hasLivePayload && Number(acceptedCount) > 0 ? 'badge-safe' : 'badge-cached'),
        metric('Unresolved Visible', unresolvedCount, hasLivePayload ? 'badge-budget-guarded' : 'badge-cached'),
        metric('Queries', queryCount, 'badge-cached')
      ].join('');
    }

    if (providers) providers.innerHTML = providerBreakdownHtml(payload);
    if (rejections) rejections.innerHTML = rejectionSummaryHtml(payload);
  }

  function wrapLoadJobs() {
    if (typeof window.loadJobs !== 'function') return;
    if (window.loadJobs.__liveTruthWrapped) return;

    const original = window.loadJobs;
    window.loadJobs = async function wrappedLoadJobs(...args) {
      const result = await original.apply(this, args);
      setTimeout(renderLiveTruthTelemetry, 0);
      return result;
    };
    window.loadJobs.__liveTruthWrapped = true;
  }

  function boot() {
    hideBoilerplateTelemetry();
    ensurePanel();
    wrapLoadJobs();
    renderLiveTruthTelemetry();

    document.addEventListener('click', function (event) {
      const target = event.target;
      if (!target) return;
      if (target.id === 'prepare-discovery-btn' || target.id === 'trigger-discovery-btn') {
        setTimeout(renderLiveTruthTelemetry, 3000);
        setTimeout(renderLiveTruthTelemetry, 9000);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  window.renderLiveTruthTelemetry = renderLiveTruthTelemetry;
})();
JS

echo
echo "=== S3: Load telemetry module in index.html ==="
python3 - <<'PY'
from pathlib import Path

p = Path("web/templates/index.html")
text = p.read_text(encoding="utf-8")

script = '    <script src="/static/js/live_truth_telemetry.js"></script>'

if "live_truth_telemetry.js" not in text:
    if "</body>" not in text:
        raise SystemExit("index.html missing </body>")
    text = text.replace("</body>", script + "\n</body>", 1)

p.write_text(text, encoding="utf-8")
PY

echo
echo "=== S4: Post-patch inspection ==="
grep -Rni "live_truth_telemetry.js\|Live Pipeline Truth\|NO FAKE SSE\|replaced-by-live-truth-telemetry\|Pipeline reactor initialized\|Rendering static telemetry readiness" \
  web/templates/index.html web/static/js/live_truth_telemetry.js web/static/js web/templates 2>/dev/null || true

echo
echo "=== S5: Compile Python ==="
python3 -m py_compile $(git ls-files '*.py')

echo
echo "=== S6: Local Flask proof, no live /api/jobs ==="
python3 - <<'PY'
from app import app

c = app.test_client()

for path in ["/", "/api/health", "/api/usage", "/api/jobs?dry_run=1", "/static/js/live_truth_telemetry.js"]:
    r = c.get(path)
    print(path, r.status_code, r.content_type)
    assert r.status_code == 200

html = c.get("/").get_data(as_text=True)
assert "live_truth_telemetry.js" in html

js = c.get("/static/js/live_truth_telemetry.js").get_data(as_text=True)
assert "Live Pipeline Truth" in js
assert "NO FAKE SSE" in js
assert "Pipeline reactor initialized" not in js
assert "Rendering static telemetry readiness" not in js
assert "/api/jobs?dry_run=1" in js
assert "provider_breakdown" in js

print("PASS: boilerplate telemetry is replaced by live-truth telemetry module.")
PY

echo
echo "=== S7: Diff proof ==="
git diff -- web/templates/index.html web/static/js/live_truth_telemetry.js
git diff --check

echo
echo "=== S8-S10: Commit and push ==="
git add web/templates/index.html web/static/js/live_truth_telemetry.js
git commit -m "Replace boilerplate telemetry with live truth panel"
git push origin main

echo
echo "=== S11: Wait for deploy trigger ==="
sleep 120

echo
echo "=== S12: Verify Cloud Run health and live JS ==="
SERVICE_URL="$(gcloud run services describe "$SERVICE" --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')"
echo "SERVICE_URL=$SERVICE_URL"

gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format="table(status.url,status.latestReadyRevisionName,status.traffic[0].revisionName,status.traffic[0].percent)"

curl -fsS "$SERVICE_URL/api/health"
echo

echo
echo "=== Live page proof ==="
curl -fsS "$SERVICE_URL/?v=$(date +%s)" \
  | grep -oE 'live_truth_telemetry.js' \
  | sort | uniq -c || true

echo
echo "=== Live telemetry JS proof ==="
curl -fsS "$SERVICE_URL/static/js/live_truth_telemetry.js?v=$(date +%s)" \
  | grep -E "Live Pipeline Truth|NO FAKE SSE|provider_breakdown|replaced-by-live-truth-telemetry" || true

echo
echo "OPEN:"
echo "$SERVICE_URL/?v=live-truth-telemetry-$(date +%s)"
echo
echo "After opening, press Run Live Discovery. The panel should show raw candidates, accepted, unresolved visible, provider fan-out, and rejection reasons."
