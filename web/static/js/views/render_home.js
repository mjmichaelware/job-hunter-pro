/* views/render_home.js — Hero cockpit + live job carousel + feature grid.
   Safe: only /api/health + /api/batches. Real data only; never fabricated. */

async function loadHomeView() {
  const el = mount(); if (!el) return;
  el.innerHTML = '<p class="state-loading">Loading…</p>';

  const [health, batchList] = await Promise.all([
    safeFetch('/api/health'),
    safeFetch('/api/batches'),
  ]);
  const batches = arr(batchList, ['batches']);
  const ok = health && (health.status === 'ok' || health.status === 'healthy');
  const ver = health && health.version ? health.version : null;

  // Pull up to 5 jobs from the most recent batch for the carousel
  let recentJobs = [];
  if (batches.length) {
    try {
      const snap = await safeFetch('/api/batches/' + encodeURIComponent(batches[0].id || batches[0]));
      recentJobs = arr(snap, ['data', 'jobs', 'accepted', 'results']).slice(0, 5);
    } catch (e) {}
  }

  const statusBadge = ok
    ? '<span class="badge badge-safe">system ok</span>'
    : '<span class="badge badge-error">backend unreachable</span>';

  // Hero
  let html = '<section class="home">'
    + '<div class="home__hero">'
    + '<div class="home__hero-inner">'
    + '<h1 class="home__logo">Job Hunter Pro</h1>'
    + '<p class="home__cycle"><span class="home__cycle-text">Discover. Resolve. Track. Get hired.</span></p>'
    + '<div class="home__badges">' + statusBadge
    + (ver ? ' <span class="badge badge-cached">v' + esc(ver) + '</span>' : '') + '</div>'
    + '</div></div>';

  // Job carousel from most recent batch
  html += '<div class="home__section-label">Recently discovered jobs</div>';
  if (recentJobs.length) {
    html += '<div class="bento-rail home__rail">'
      + recentJobs.map(function (j) {
          const co = esc(cleanText(j.company || j.company_name, ''));
          const src = esc(j.source || j._provider || j.via || '');
          return '<div class="home__slide bento">'
            + '<div class="home__slide-title">' + esc(j.title || 'Untitled') + '</div>'
            + (co ? '<div class="home__slide-co">' + co + '</div>' : '')
            + (src ? '<span class="tag">' + src + '</span>' : '')
            + '</div>';
        }).join('')
      + '</div>';
  } else {
    html += '<div class="info-box">No saved jobs yet — run discovery to populate this feed.</div>';
  }

  // Feature marketing grid
  const features = [
    { icon: '🔍', label: 'Multi-source discovery', sub: '20+ free job APIs, auto-fanout', go: 'discovery' },
    { icon: '📍', label: 'Address resolution', sub: 'Commute, radius, maps links', go: 'jobs' },
    { icon: '🧠', label: 'AI enrichment', sub: 'Scoring, classification, gap-fill', go: 'providers' },
    { icon: '📋', label: 'Apply tracker', sub: 'Track every application', go: 'applications' },
  ];
  html += '<div class="home__section-label">What this does</div>'
    + '<div class="card-row card-row--4">'
    + features.map(function (f) {
        return '<button type="button" class="stat-card stat-card--link home__feat" data-go="' + esc(f.go) + '">'
          + '<div class="home__feat-icon">' + f.icon + '</div>'
          + '<div class="stat-card__label">' + esc(f.label) + '</div>'
          + '<div class="home__feat-sub">' + esc(f.sub) + '</div>'
          + '</button>';
      }).join('')
    + '</div>';

  // Quick-stat row
  html += '<div class="home__section-label">Quick stats</div>'
    + '<div class="card-row">'
    + _homeCard('jobs', 'Saved batches', String(batches.length), batches.length ? 'tap to browse' : 'run discovery first')
    + _homeCard('discovery', 'Discovery', '▶', 'run a fresh search')
    + _homeCard('history', 'History', '⤓', 'timeline & counts')
    + _homeCard('diagnostics', 'System', ver ? '✓' : '—', ver ? 'v' + ver : 'check diagnostics')
    + '</div>'
    + '</section>';

  el.innerHTML = html;
  el.querySelectorAll('[data-go]').forEach(function (c) {
    c.addEventListener('click', function () { navigate(c.dataset.go); });
  });
}

function _homeCard(target, label, value, sub) {
  return '<button type="button" class="stat-card stat-card--link" data-go="' + esc(target) + '">'
    + '<div class="stat-card__label">' + esc(label) + '</div>'
    + '<div class="stat-card__value">' + esc(value) + '</div>'
    + '<div class="stat-card__sub">' + esc(sub) + '</div></button>';
}

registerView('home', 'Home', loadHomeView);
