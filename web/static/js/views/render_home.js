/* views/render_home.js — Home overview. Safe: only /api/health + /api/batches.
   Real counts only; missing → honest dashes. Cards route to their views. */

async function loadHomeView() {
  const el = mount(); if (!el) return;
  el.innerHTML = '<p class="state-loading">Loading overview…</p>';

  const [health, batchList] = await Promise.all([
    safeFetch('/api/health'),
    safeFetch('/api/batches'),
  ]);
  const batches = arr(batchList, ['batches']);

  // accepted-job count across saved batches is unknown without per-batch reads;
  // show batch count (real) and a live status, never a fabricated job number.
  const batchCount = batches.length;
  const ver = health && health.version ? esc(health.version) : null;
  const ok = health && (health.status === 'ok' || health.status === 'healthy');

  function card(target, label, value, sub) {
    return '<button type="button" class="stat-card stat-card--link" data-go="' + esc(target) + '">'
      + '<div class="stat-card__label">' + esc(label) + '</div>'
      + '<div class="stat-card__value">' + value + '</div>'
      + (sub ? '<div class="stat-card__sub">' + esc(sub) + '</div>' : '') + '</button>';
  }

  el.innerHTML = '<section class="home">'
    + '<div class="home__hero glass"><h2>Job Hunter Pro</h2>'
    + '<p class="status-line">' + esc(t('home.tag')) + '</p>'
    + '<p class="status-line">' + (ok ? '<span class="badge badge-safe">system ok</span>' : '<span class="badge badge-error">backend unreachable</span>')
    + ' <span class="badge badge-safe">safe — opening this spends nothing</span></p></div>'
    + '<div class="card-row">'
    + card('jobs', 'Saved batches', String(batchCount), batchCount ? 'tap to browse jobs' : 'run discovery to create one')
    + card('discovery', 'Discovery', '▶', 'run a fresh search')
    + card('history', 'History', '⤓', 'timeline & counts')
    + card('diagnostics', 'System', ver ? '✓' : '—', ver ? ('v' + ver) : 'diagnostics')
    + '</div></section>';

  el.querySelectorAll('[data-go]').forEach(function (c) {
    c.addEventListener('click', function () { navigate(c.dataset.go); });
  });
}

registerView('home', 'Home', loadHomeView);
