/* views/render_debug.js — Pipeline funnel + provider breakdown + API readiness
   checklist + system to-do list. Raw JSON only in collapsed details. */

async function loadDebugView() {
  const el = mount(); if (!el) return;
  el.innerHTML = '<p class="state-loading">Loading diagnostics…</p>';

  const [debugData, provData] = await Promise.all([
    safeFetch('/api/debug/jobs'),
    safeFetch('/api/providers'),
  ]);

  JHP_SYNC.remember('debug', debugData);
  const data = debugData || {};
  const counts = { raw: data.raw_count, accepted: data.accepted_count, rejected: data.rejected_count, queries: data.query_count };
  const hasCounts = Object.keys(counts).some(function (k) { return counts[k] != null; });

  let html = '';

  // Pipeline funnel
  if (hasCounts) {
    html += '<h2 class="section-heading">Pipeline funnel</h2>'
      + cssBars([
          { label: 'Raw fetched', value: counts.raw },
          { label: 'Accepted', value: counts.accepted },
          { label: 'Flagged', value: counts.rejected },
        ], { empty: 'No pipeline data yet. Run discovery first.' });
    html += '<div class="card-row">'
      + Object.keys(counts).map(function (k) {
          return '<div class="stat-card"><div class="stat-card__label">' + esc(k) + '</div>'
            + '<div class="stat-card__value">'
            + (counts[k] != null ? esc(String(counts[k])) : '<span class="na">—</span>')
            + '</div></div>';
        }).join('') + '</div>';
  } else {
    html += '<div class="info-box">No pipeline data yet. Run fresh discovery to populate this view.</div>';
  }

  // Provider breakdown
  const pb = data.provider_breakdown || {};
  if (Object.keys(pb).length) {
    html += '<h2 class="section-heading">Provider breakdown</h2>'
      + '<table class="data-table"><thead><tr><th>Provider</th><th>Status</th><th>Raw</th><th>Queries</th></tr></thead><tbody>'
      + Object.entries(pb).map(function (kv) {
          const v = kv[1] || {};
          return '<tr><td>' + esc(v.label || kv[0]) + '</td>'
            + '<td><span class="badge ' + (v.available ? 'badge-safe' : 'badge-disabled') + '">'
            + esc(v.status || (v.available ? 'available' : 'unavailable')) + '</span></td>'
            + '<td>' + (v.raw_count != null ? esc(String(v.raw_count)) : '—') + '</td>'
            + '<td>' + (v.queries_attempted != null ? esc(String(v.queries_attempted)) : '—') + '</td></tr>';
        }).join('') + '</tbody></table>';
  }

  // Rejection summary
  const rs = data.rejection_summary || {};
  if (Object.keys(rs).length) html += '<h2 class="section-heading">Rejection / flag summary</h2>' + cssBars(countsToRows(rs));

  // API Readiness checklist
  const providers = provData ? (provData.providers || []) : [];
  const pList = Array.isArray(providers) ? providers : Object.values(providers);
  if (pList.length) {
    const live = pList.filter(function (p) { return p.available; });
    const needsKey = pList.filter(function (p) { return !p.available && !p.disabled_reason; });
    const defaultOff = pList.filter(function (p) { return !p.available && p.disabled_reason; });

    html += '<h2 class="section-heading">API Readiness</h2><div class="readiness-grid">';
    if (live.length) {
      html += '<div class="readiness-col"><h3 class="readiness-col__title">🟢 Live</h3>'
        + live.map(function (p) { return '<div class="readiness-item">' + esc(p.label || p.key || '') + '</div>'; }).join('') + '</div>';
    }
    if (needsKey.length) {
      html += '<div class="readiness-col"><h3 class="readiness-col__title">🔑 Needs API key</h3>'
        + needsKey.map(function (p) { return '<div class="readiness-item readiness-item--warn">' + esc(p.label || p.key || '') + '</div>'; }).join('') + '</div>';
    }
    if (defaultOff.length) {
      html += '<div class="readiness-col"><h3 class="readiness-col__title">⛔ Default-off</h3>'
        + defaultOff.map(function (p) {
            return '<div class="readiness-item readiness-item--off">'
              + esc(p.label || p.key || '') + '<span class="readiness-hint">' + esc((p.disabled_reason || '').slice(0, 60)) + '</span></div>';
          }).join('') + '</div>';
    }
    html += '</div>';

    // To-do list from disabled_reason strings
    const todos = defaultOff.filter(function (p) { return p.disabled_reason; });
    if (todos.length || needsKey.length) {
      html += '<h2 class="section-heading">System To-Do</h2><ul class="todo-list">';
      needsKey.forEach(function (p) {
        html += '<li class="todo-item">🔑 Add <code>' + esc((p.key || '').toUpperCase() + '_API_KEY') + '</code> to Secret Manager to activate <strong>' + esc(p.label || p.key) + '</strong></li>';
      });
      todos.forEach(function (p) {
        html += '<li class="todo-item">⚙️ ' + esc(p.disabled_reason) + ' (<strong>' + esc(p.label || p.key) + '</strong>)</li>';
      });
      html += '</ul>';
    }
  }

  // Raw JSON (collapsed)
  if (Object.keys(data).length) {
    html += '<details class="filter-panel"><summary>Raw debug JSON</summary>'
      + '<pre style="overflow:auto;font-size:0.75rem;color:var(--c-muted)">' + esc(JSON.stringify(data, null, 2)) + '</pre></details>';
  }

  el.innerHTML = html;
}

registerView('debug', 'Debug', loadDebugView);
