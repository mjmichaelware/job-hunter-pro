/* views/render_budget.js — quota fuel-cell + guard state.
   Fuel-cell fill = REAL usage / capacity; it cannot exceed actual spend.
   Always shows the safe-boot guarantee in plain copy. */

function _statCard(label, value) {
  return '<div class="stat-card"><div class="stat-card__label">' + esc(label) + '</div>'
    + '<div class="stat-card__value">' + (value != null && value !== '' ? esc(String(value)) : '<span class="na">' + esc(t('common.unavailable')) + '</span>') + '</div></div>';
}

function _fuelCell(used, capacity, left, guard) {
  if (used == null || capacity == null || Number(capacity) <= 0) {
    return '<div class="info-box"><span class="na">Fuel cell unavailable — usage/capacity not reported.</span></div>';
  }
  const pct = Math.max(0, Math.min(100, (Number(used) / Number(capacity)) * 100));
  const locked = (left != null && guard != null && Number(left) <= Number(guard));
  const fillCls = locked ? 'fuel__fill--locked' : pct > 80 ? 'fuel__fill--hot' : 'fuel__fill--ok';
  return '<div class="fuel" role="img" aria-label="Quota ' + Math.round(pct) + ' percent used">'
    + '<div class="fuel__bar"><div class="' + fillCls + '" style="width:' + pct.toFixed(1) + '%"></div></div>'
    + '<div class="fuel__meta">' + Math.round(pct) + '% used'
    + (locked ? ' <span class="badge badge-budget-guarded">budget guarded — discovery paused</span>' : '') + '</div></div>';
}

async function loadBudgetView() {
  const data = await safeFetch('/api/usage');
  const el = mount(); if (!el) return;
  if (!data) { renderState(el, 'state-error', 'Could not load usage data.'); return; }
  JHP_SYNC.remember('budget', data);
  const serp = data.serpapi || {}; const budget = data.budget || {}; const storage = data.storage || {};

  el.innerHTML = '<div class="card-row">'
    + _statCard('SerpAPI searches left', serp.total_searches_left)
    + _statCard('Plan', serp.plan_name)
    + _statCard('This month used', serp.this_month_usage)
    + _statCard('Searches / month', serp.searches_per_month)
    + '</div>'
    + '<h2 class="section-heading">Quota fuel cell</h2>'
    + _fuelCell(serp.this_month_usage, serp.searches_per_month, serp.total_searches_left, budget.min_searches_left_guard)
    + '<h2 class="section-heading">Budget guard</h2>'
    + '<table class="data-table"><tbody>'
    + '<tr><th>Min searches left guard</th><td>' + esc(String(budget.min_searches_left_guard != null ? budget.min_searches_left_guard : 'unavailable')) + '</td></tr>'
    + '<tr><th>Max SerpAPI queries / live run</th><td>' + esc(String(budget.max_serp_queries_per_live_run || budget.max_queries || 'unavailable')) + '</td></tr>'
    + '<tr><th>Max raw jobs / live run</th><td>' + esc(String(budget.max_raw_jobs_per_live_run || budget.max_raw_jobs || 'unavailable')) + '</td></tr>'
    + '</tbody></table>'
    + (Object.keys(storage).length ? '<h2 class="section-heading">Storage</h2><table class="data-table"><tbody>'
        + Object.entries(storage).map(function (kv) { return '<tr><th>' + esc(kv[0]) + '</th><td>' + esc(String(kv[1])) + '</td></tr>'; }).join('') + '</tbody></table>' : '')
    + '<div class="info-box"><strong>Safe by default:</strong> Opening this dashboard does not run live discovery and costs nothing. '
    + 'The "Run fresh discovery" button in the Jobs view is the only action that may spend quota.</div>';
}

registerView('budget', 'Budget', loadBudgetView);
