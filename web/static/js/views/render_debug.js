/* views/render_debug.js — pipeline funnel + provider breakdown + rejection/flag
   summaries. Raw JSON only inside a collapsed <details>, never the primary UI. */

async function loadDebugView() {
  const data = await safeFetch('/api/debug/jobs');
  const el = mount(); if (!el) return;
  if (!data) { renderState(el, 'state-error', 'Could not load debug data. /api/debug/jobs may be unavailable.'); return; }
  JHP_SYNC.remember('debug', data);

  const counts = { raw: data.raw_count, accepted: data.accepted_count, rejected: data.rejected_count, queries: data.query_count };
  const hasCounts = Object.keys(counts).some(function (k) { return counts[k] != null; });
  let html = '<h2 class="section-heading">Pipeline reactor</h2>' + renderReactorShell();
  html += '<h2 class="section-heading">Geo radar</h2>' + renderGeoRadar(arr(data, ['accepted', 'data']));

  if (hasCounts) {
    html += '<h2 class="section-heading">Pipeline funnel</h2>'
      + cssBars([
          { label: 'Raw', value: counts.raw },
          { label: 'Accepted', value: counts.accepted },
          { label: 'Rejected', value: counts.rejected },
        ], { empty: 'No pipeline counts yet.' });
    html += '<div class="card-row">'
      + Object.keys(counts).map(function (k) {
          return '<div class="stat-card"><div class="stat-card__label">' + esc(k) + '</div><div class="stat-card__value">' + (counts[k] != null ? esc(String(counts[k])) : '<span class="na">—</span>') + '</div></div>';
        }).join('') + '</div>';
  }

  const pb = data.provider_breakdown || {};
  if (Object.keys(pb).length) {
    html += '<h2 class="section-heading">Provider breakdown</h2>'
      + '<table class="data-table"><thead><tr><th>Provider</th><th>Status</th><th>Raw</th><th>Queries</th></tr></thead><tbody>'
      + Object.entries(pb).map(function (kv) {
          const v = kv[1] || {};
          return '<tr><td>' + esc(v.label || kv[0]) + '</td>'
            + '<td><span class="badge ' + (v.available ? 'badge-safe' : 'badge-disabled') + '">' + esc(v.status || (v.available ? 'available' : 'unavailable')) + '</span></td>'
            + '<td>' + (v.raw_count != null ? esc(String(v.raw_count)) : '—') + '</td>'
            + '<td>' + (v.queries_attempted != null ? esc(String(v.queries_attempted)) : '—') + '</td></tr>';
        }).join('') + '</tbody></table>';
  }

  const rs = data.rejection_summary || {};
  if (Object.keys(rs).length) html += '<h2 class="section-heading">Rejection reasons</h2>' + cssBars(countsToRows(rs));
  const rfs = data.resolution_flag_summary || {};
  if (Object.keys(rfs).length) html += '<h2 class="section-heading">Resolution flags</h2>' + cssBars(countsToRows(rfs));

  if (!hasCounts && !Object.keys(pb).length && !Object.keys(rs).length) {
    html += '<p class="state-empty">No debug data available. Run a discovery batch first.</p>';
  } else {
    html += '<details class="filter-panel"><summary>Raw debug JSON</summary><pre style="overflow:auto;font-size:0.75rem;color:var(--c-muted)">' + esc(JSON.stringify(data, null, 2)) + '</pre></details>';
  }
  el.innerHTML = html;
  connectPipeline(el);  // real SSE if available, honest "unavailable" otherwise
}

registerView('debug', 'Debug', loadDebugView);
