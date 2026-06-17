/* views/render_history.js — batch timeline + per-batch counts + accepted/rejected bars. */

async function loadHistoryView() {
  const data = await safeFetch('/api/history?hours=168');
  const el = mount(); if (!el) return;
  if (!data) { renderState(el, 'state-error', 'Could not load history.'); return; }
  JHP_SYNC.remember('history', data);
  const batches = arr(data, ['batches']);

  let html = '';
  if (data.batch_count != null || data.job_count != null) {
    html += '<div class="card-row">'
      + (data.batch_count != null ? '<div class="stat-card"><div class="stat-card__label">Total batches</div><div class="stat-card__value">' + esc(String(data.batch_count)) + '</div></div>' : '')
      + (data.job_count != null ? '<div class="stat-card"><div class="stat-card__label">Total jobs stored</div><div class="stat-card__value">' + esc(String(data.job_count)) + '</div></div>' : '')
      + '</div>';
  }

  if (!batches.length) {
    html += '<p class="state-empty">No batch history exists yet. Run a discovery to create the first batch.</p>';
    el.innerHTML = html; return;
  }

  // accepted-per-batch chart from real counts
  const rows = batches.map(function (b) {
    return { label: (b.created_at_utc || b.object_name || '—').slice(0, 16), value: (b.counts || {}).accepted };
  }).filter(function (r) { return r.value != null; });
  if (rows.length) html += '<h2 class="section-heading">Accepted per batch</h2>' + cssBars(rows, { empty: 'No accepted counts recorded yet.' });

  html += '<h2 class="section-heading">Batches</h2><table class="data-table">'
    + '<thead><tr><th>Batch</th><th>Created</th><th>Accepted</th><th>Rejected</th><th>Raw</th><th>Queries</th></tr></thead><tbody>';
  batches.forEach(function (b) {
    const c = b.counts || {};
    html += '<tr><td><code class="batch-id">' + esc(b.object_name || b.batch_id || '—') + '</code></td>'
      + '<td>' + esc(b.created_at_utc || b.updated || '—') + '</td>'
      + '<td>' + (c.accepted != null ? esc(String(c.accepted)) : '—') + '</td>'
      + '<td>' + (c.rejected != null ? esc(String(c.rejected)) : '—') + '</td>'
      + '<td>' + (c.raw != null ? esc(String(c.raw)) : '—') + '</td>'
      + '<td>' + (c.queries != null ? esc(String(c.queries)) : '—') + '</td></tr>';
  });
  html += '</tbody></table>';
  el.innerHTML = html;
}

registerView('history', 'History', loadHistoryView);
