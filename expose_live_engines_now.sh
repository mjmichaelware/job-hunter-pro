#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="ai-job-agent-498702"
REGION="us-central1"
SERVICE="job-hunter-pro"

fail(){ echo "FAIL: $1"; exit 1; }

echo "=== EXPOSE LIVE ENGINES NOW ==="
echo "This keeps safe boot safe, but exposes live controls and proves live /api/jobs once."
echo "PWD=$(pwd)"
echo

[ -f app.py ] || fail "app.py missing; not repo root"
[ -f web/templates/index.html ] || fail "missing web/templates/index.html"

echo "=== 1) Inspect hidden live controls and engine routes ==="
grep -Rni "prepare-discovery-btn\|trigger-discovery-btn\|live-action-guard\|display:none\|/api/jobs\|/api/opportunities\|/api/providers\|/api/_surface" \
  web/templates/index.html web/static/js app.py api 2>/dev/null || true

echo
echo "=== 2) Create live engine bridge JS ==="
cat > web/static/js/live_engine_bridge.js <<'JS'
(function () {
  const SAFE_ENDPOINTS = [
    ['/api/health', 'Health'],
    ['/api/usage', 'Usage/Budget'],
    ['/api/jobs?dry_run=1', 'Jobs Dry Run'],
    ['/api/opportunities', 'Opportunities'],
    ['/api/history', 'History'],
    ['/api/providers', 'Providers'],
    ['/api/industries', 'Industries'],
    ['/api/_surface', 'Surface Map']
  ];

  function e(value) {
    if (window.escapeHtml) return window.escapeHtml(value);
    return String(value ?? '').replace(/[&<>"']/g, (ch) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
  }

  async function fetchJson(path) {
    try {
      const res = await fetch(path, { cache: 'no-store' });
      const text = await res.text();
      let json = null;
      try { json = JSON.parse(text); } catch (_) {}
      return { path, ok: res.ok, status: res.status, json, text };
    } catch (err) {
      return { path, ok: false, status: 0, error: String(err) };
    }
  }

  function countPayload(payload, keys) {
    if (!payload || typeof payload !== 'object') return 0;
    for (const key of keys) {
      const value = payload[key];
      if (Array.isArray(value)) return value.length;
      if (typeof value === 'number') return value;
    }
    if (Array.isArray(payload.data)) return payload.data.length;
    if (payload.data && typeof payload.data === 'object') {
      for (const key of keys) {
        const value = payload.data[key];
        if (Array.isArray(value)) return value.length;
        if (typeof value === 'number') return value;
      }
    }
    return 0;
  }

  function ensureLiveButton() {
    let btn = document.getElementById('prepare-discovery-btn');
    const header = document.querySelector('#header > div') || document.getElementById('header');

    if (!btn && header) {
      btn = document.createElement('button');
      btn.id = 'prepare-discovery-btn';
      btn.className = 'badge badge-live';
      btn.type = 'button';
      header.appendChild(btn);
    }

    if (btn) {
      btn.textContent = 'Run Live Discovery';
      btn.style.display = 'inline-flex';
      btn.style.cursor = 'pointer';
      btn.removeAttribute('hidden');
      btn.disabled = false;
      btn.setAttribute('aria-label', 'Run live discovery. This may use discovery provider budget.');
    }

    const guard = document.getElementById('live-action-guard');
    if (guard) {
      guard.style.display = 'flex';
      guard.innerHTML = '<span class="badge badge-live">LIVE ACTION READY</span><span>Run Live Discovery calls /api/jobs and may use discovery provider budget. Page load remains safe.</span>';
    }

    const trigger = document.getElementById('trigger-discovery-btn');
    if (trigger) {
      trigger.style.display = 'inline-flex';
      trigger.textContent = 'Confirm Live Discovery';
      trigger.disabled = false;
    }

    return btn;
  }

  function ensureSurfacePanel() {
    const overview = document.getElementById('tab-overview');
    if (!overview) return null;

    let panel = document.getElementById('live-engine-surface');
    if (!panel) {
      panel = document.createElement('section');
      panel.id = 'live-engine-surface';
      panel.className = 'card';
      panel.innerHTML = `
        <div style="display:flex;justify-content:space-between;gap:var(--space-md);align-items:flex-start;flex-wrap:wrap;">
          <div>
            <h3>Live Engine Surface</h3>
            <p class="muted">Mounted routes, safe endpoints, provider state, and explicit live action status.</p>
          </div>
          <span class="badge badge-safe">SAFE BOOT</span>
        </div>
        <div id="live-engine-summary" class="grid-overview" style="margin-top:var(--space-md);"></div>
        <div id="live-engine-endpoints" style="margin-top:var(--space-md);"></div>
      `;
      overview.insertBefore(panel, overview.firstChild);
    }
    return panel;
  }

  function metric(label, value, badgeClass) {
    return `<div class="card"><div class="metric-label">${e(label)}</div><div class="metric-num">${e(value)}</div>${badgeClass ? `<span class="badge ${badgeClass}">${e(badgeClass.replace('badge-', ''))}</span>` : ''}</div>`;
  }

  async function refreshSurfacePanel() {
    const panel = ensureSurfacePanel();
    if (!panel) return;

    const summary = document.getElementById('live-engine-summary');
    const endpoints = document.getElementById('live-engine-endpoints');

    const results = await Promise.all(SAFE_ENDPOINTS.map(([path]) => fetchJson(path)));
    const byPath = Object.fromEntries(results.map(r => [r.path, r]));

    const health = byPath['/api/health']?.json;
    const usage = byPath['/api/usage']?.json;
    const dry = byPath['/api/jobs?dry_run=1']?.json;
    const opps = byPath['/api/opportunities']?.json;
    const hist = byPath['/api/history']?.json;
    const providers = byPath['/api/providers']?.json;

    const oppCount = countPayload(opps, ['opportunities', 'data', 'count']);
    const batchCount = countPayload(hist, ['batches', 'history', 'batch_count']);
    const providerCount = countPayload(providers, ['providers', 'data', 'count']);

    const serpLeft =
      usage?.total_searches_left ??
      usage?.serpapi?.total_searches_left ??
      usage?.serpapi?.searches_left ??
      usage?.serpapi?.remaining ??
      '—';

    summary.innerHTML = [
      metric('Health', health?.status || 'unknown', health?.status === 'ok' ? 'badge-safe' : 'badge-budget-guarded'),
      metric('SerpAPI Left', serpLeft, 'badge-cached'),
      metric('Opportunities', oppCount || '—', oppCount ? 'badge-safe' : 'badge-cached'),
      metric('Batches', batchCount, 'badge-cached'),
      metric('Providers', providerCount || 'visible', 'badge-cached'),
      metric('Jobs Dry Run', dry?.dry_run ? 'ready' : (dry?.status || 'unknown'), 'badge-safe')
    ].join('');

    endpoints.innerHTML = `
      <table>
        <thead><tr><th>Endpoint</th><th>Status</th><th>Meaning</th></tr></thead>
        <tbody>
          ${results.map((r, idx) => {
            const [path, label] = SAFE_ENDPOINTS[idx];
            let meaning = 'safe probe';
            if (path === '/api/jobs?dry_run=1') meaning = 'query plan only; does not run live discovery';
            if (path === '/api/opportunities') meaning = `${countPayload(r.json, ['opportunities', 'data', 'count']) || 0} opportunity records visible`;
            if (path === '/api/history') meaning = `${countPayload(r.json, ['batches', 'history', 'batch_count']) || 0} stored batches visible`;
            if (path === '/api/_surface') meaning = 'backend surface map if implemented';
            return `<tr><td><code>${e(path)}</code></td><td><span class="badge ${r.ok ? 'badge-safe' : 'badge-budget-guarded'}">${e(r.status)}</span></td><td>${e(label)} — ${e(meaning)}</td></tr>`;
          }).join('')}
        </tbody>
      </table>
    `;
  }

  async function runLiveDiscovery() {
    const ok = window.confirm(
      'Run live discovery now?\n\nThis calls /api/jobs and may use discovery provider budget. It is not run on page load.'
    );
    if (!ok) return;

    const btn = ensureLiveButton();
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Running Live Discovery...';
    }

    try {
      if (window.AppState && typeof AppState.setTab === 'function') {
        AppState.setTab('live_jobs');
      }

      if (typeof loadJobs === 'function') {
        await loadJobs({ live: true });
      } else {
        const data = await fetchJson('/api/jobs');
        const container = document.getElementById('jobs-container');
        if (container) {
          container.innerHTML = `<pre>${e(JSON.stringify(data.json || data.text || data.error, null, 2))}</pre>`;
        }
      }

      await refreshSurfacePanel();
    } catch (err) {
      console.error(err);
      const container = document.getElementById('jobs-container');
      if (container) container.innerHTML = '<div class="chart-fallback">Live discovery failed. Check Cloud Run logs and /api/health.</div>';
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Run Live Discovery';
      }
    }
  }

  function boot() {
    const btn = ensureLiveButton();
    if (btn && !btn.dataset.liveBound) {
      btn.dataset.liveBound = '1';
      btn.addEventListener('click', runLiveDiscovery);
    }

    const trigger = document.getElementById('trigger-discovery-btn');
    if (trigger && !trigger.dataset.liveBound) {
      trigger.dataset.liveBound = '1';
      trigger.addEventListener('click', runLiveDiscovery);
    }

    refreshSurfacePanel();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  window.refreshLiveEngineSurface = refreshSurfacePanel;
})();
JS

echo
echo "=== 3) Ensure script is loaded and live controls are visible ==="
python3 - <<'PY'
from pathlib import Path

p = Path("web/templates/index.html")
text = p.read_text(encoding="utf-8")

if "live_engine_bridge.js" not in text:
    text = text.replace("</body>", '    <script src="/static/js/live_engine_bridge.js"></script>\n</body>', 1)

text = text.replace(
    'id="prepare-discovery-btn" class="badge badge-live" style="cursor:pointer;display:none;"',
    'id="prepare-discovery-btn" class="badge badge-live" style="cursor:pointer;display:inline-flex;"'
)

text = text.replace(
    'id="live-action-guard" style="display:none;',
    'id="live-action-guard" style="display:flex;'
)

p.write_text(text, encoding="utf-8")
PY

echo
echo "=== 4) Post-patch inspection ==="
grep -Rni "live_engine_bridge.js\|prepare-discovery-btn\|live-action-guard\|Run Live Discovery\|runLiveDiscovery\|/api/jobs" \
  web/templates/index.html web/static/js/live_engine_bridge.js web/static/js/render_jobs.js || true

echo
echo "=== 5) Compile locally ==="
python3 -m py_compile $(git ls-files '*.py')

echo
echo "=== 6) Local proof: safe endpoints only ==="
python3 - <<'PY'
from app import app

c = app.test_client()

for path in ["/", "/api/health", "/api/usage", "/api/jobs?dry_run=1", "/api/opportunities", "/api/history", "/static/js/live_engine_bridge.js"]:
    r = c.get(path)
    print(path, r.status_code, r.content_type)
    assert r.status_code == 200

html = c.get("/").get_data(as_text=True)
assert "live_engine_bridge.js" in html
assert "prepare-discovery-btn" in html
assert "display:inline-flex" in html

js = c.get("/static/js/live_engine_bridge.js").get_data(as_text=True)
assert "Run live discovery now?" in js
assert "/api/jobs" in js
assert "/api/jobs?dry_run=1" in js

print("PASS: live engines surfaced; safe boot still does not call live /api/jobs.")
PY

echo
echo "=== 7) Diff proof ==="
git diff -- web/templates/index.html web/static/js/live_engine_bridge.js
git diff --check

echo
echo "=== 8) Commit and push ==="
git add web/templates/index.html web/static/js/live_engine_bridge.js
git commit -m "S10 surface live engines and explicit discovery action"
git push origin main

echo
echo "=== 9) Wait for deploy trigger ==="
sleep 120

echo
echo "=== 10) Verify Cloud Run ==="
SERVICE_URL="$(gcloud run services describe "$SERVICE" --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')"
echo "SERVICE_URL=$SERVICE_URL"

gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format="table(status.url,status.latestReadyRevisionName,status.traffic[0].revisionName,status.traffic[0].percent)"

echo
echo "=== 11) Health ==="
curl -fsS "$SERVICE_URL/api/health"
echo

echo
echo "=== 12) Live UI proof ==="
curl -fsS "$SERVICE_URL/?v=$(date +%s)" \
  | grep -oE 'live_engine_bridge.js|prepare-discovery-btn|Run Live Discovery|display:inline-flex|live-action-guard' \
  | sort | uniq -c || true

echo
echo "=== 13) Live JS proof ==="
curl -fsS "$SERVICE_URL/static/js/live_engine_bridge.js?v=$(date +%s)" \
  | grep -E "Run live discovery now|/api/jobs|/api/jobs\?dry_run=1|Live Engine Surface" || true

echo
echo "=== 14) EXPLICIT LIVE /api/jobs PROOF — THIS MAY SPEND DISCOVERY BUDGET ==="
curl -sS -o /tmp/live_jobs_now.json -w "HTTP %{http_code}\n" "$SERVICE_URL/api/jobs"
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/tmp/live_jobs_now.json")
text = p.read_text(errors="replace")
print(text[:800])
try:
    data = json.loads(text)
    print()
    print("TOP_KEYS=", sorted(data.keys()) if isinstance(data, dict) else type(data).__name__)
    if isinstance(data, dict):
        for key in ["jobs", "data", "accepted", "results", "count", "raw_count", "status", "message", "budget"]:
            if key in data:
                v = data[key]
                if isinstance(v, list):
                    print(key, "LIST_LEN", len(v))
                elif isinstance(v, dict):
                    print(key, "DICT_KEYS", sorted(v.keys()))
                else:
                    print(key, repr(v))
except Exception as e:
    print("JSON_PARSE_ERROR", e)
PY

echo
echo "OPEN:"
echo "$SERVICE_URL/?v=live-engines-$(date +%s)"
