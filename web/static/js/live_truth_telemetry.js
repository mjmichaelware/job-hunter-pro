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
