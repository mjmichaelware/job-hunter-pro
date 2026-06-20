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
    + '<div class="hero">'
    + '<div class="hero__art">' + icon('rocket', { size: 52 }) + '</div>'
    + '<h1 class="hero__title">Job Hunter Pro</h1>'
    + '<p class="hero__sub">Your local opportunity cockpit — discover jobs across 20+ free sources, '
    + 'resolve real addresses and commute, score the match, and track every application in one place.</p>'
    + '<div class="hero__live"><span class="hero__stat flash"><b>' + batches.length + '</b> batches saved</span>'
    + '<span class="hero__stat flash"><b>' + recentJobs.length + '</b> recent jobs</span></div>'
    + '<div class="hero__badges">' + statusBadge
    + (ver ? ' <span class="badge badge-cached">v' + esc(ver) + '</span>' : '')
    + ' <span class="badge badge-safe">free to use</span></div>'
    + '<details class="hero__more"><summary class="hero__more-toggle">Read more about how this works</summary>'
    + '<div class="hero__more-body">'
    + '<p><strong>1 · Discover.</strong> One run fans out across every configured free source — '
    + 'SerpAPI Jobs, Adzuna, USAJobs, Jooble, Careerjet, The Muse and more — giving each a fair turn so no single provider hogs the results.</p>'
    + '<p><strong>2 · Resolve.</strong> Each listing is matched to a real business and address; Google Maps adds commute and radius from your origin. '
    + 'When an address can\'t be pinned the job is kept and flagged — never silently dropped.</p>'
    + '<p><strong>3 · Score &amp; classify.</strong> A match score, a capped review score, and an industry tag are computed deterministically; '
    + 'AI providers (OpenAI, Gemini, Claude, Groq, xAI) only enrich and explain — they never invent listings.</p>'
    + '<p><strong>4 · Remember.</strong> Every run is stored as a timestamped batch you can browse offline, with the full accepted / flagged breakdown and the evidence behind each decision.</p>'
    + '<p><strong>5 · Apply &amp; track.</strong> Vet any employer in one tap (Glassdoor, BBB, Google, News, Indeed, Maps) and track every application from one place.</p>'
    + '<p class="hero__more-note">Opening this dashboard spends nothing. Live discovery runs only when you ask for it.</p>'
    + '</div></details>'
    + '</div>';

  // Job carousel from most recent batch
  html += '<div class="home__section-label">Recently discovered jobs</div>';
  if (recentJobs.length) {
    html += '<div class="home__carousel">'
      + '<div class="bento-rail home__rail" id="home-rail">'
      + recentJobs.map(function (j) {
          const co = esc(cleanText(j.company || j.company_name, ''));
          const src = esc(j.source || j._provider || j.via || '');
          return '<div class="home__slide bento">'
            + '<div class="home__slide-title">' + esc(j.title || 'Untitled') + '</div>'
            + (co ? '<div class="home__slide-co">' + co + '</div>' : '')
            + (src ? '<span class="tag">' + src + '</span>' : '')
            + '</div>';
        }).join('')
      + '</div>'
      + '<div class="home__carousel-nav">'
      + '<button class="home__carousel-btn" id="carousel-prev" aria-label="Previous">&#8249;</button>'
      + '<div class="home__carousel-dots" id="carousel-dots"></div>'
      + '<button class="home__carousel-btn" id="carousel-next" aria-label="Next">&#8250;</button>'
      + '</div></div>';
  } else {
    html += '<div class="info-box">No saved jobs yet — run discovery to populate this feed.</div>';
  }

  // Feature marketing grid
  const features = [
    { ic: 'discovery', label: 'Multi-source discovery', sub: '20+ free job APIs, fair fan-out', go: 'discovery' },
    { ic: 'pin', label: 'Address resolution', sub: 'Commute, radius & map links', go: 'jobs' },
    { ic: 'spark', label: 'AI enrichment', sub: 'Scoring, classification, gap-fill', go: 'providers' },
    { ic: 'applications', label: 'Apply tracker', sub: 'Track every application', go: 'applications' },
  ];
  html += '<div class="home__section-label">What this does</div>'
    + '<div class="card-row card-row--4 stagger-in">'
    + features.map(function (f) {
        return '<button type="button" class="stat-card stat-card--link feature-card" data-go="' + esc(f.go) + '">'
          + '<span class="feature-card__icon">' + icon(f.ic, { size: 22 }) + '</span>'
          + '<div class="feature-card__title">' + esc(f.label) + '</div>'
          + '<div class="feature-card__sub">' + esc(f.sub) + '</div>'
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
  if (typeof applyIndustry === 'function') applyIndustry(null);  // neutral accent on home
  // Living background: intensity from REAL state (system ok + how much history exists).
  if (typeof updateVolumetric === 'function') {
    const intensity = (ok ? 0.4 : 0.15) + Math.min(0.5, batches.length / 20);
    updateVolumetric({ intensity: intensity });
  }
  el.querySelectorAll('[data-go]').forEach(function (c) {
    c.addEventListener('click', function () { navigate(c.dataset.go); });
  });
  if (recentJobs.length > 1) _carousel(el, recentJobs.length);
}

function _carousel(el, n) {
  const rail = el.querySelector('#home-rail'), dots = el.querySelector('#carousel-dots');
  if (!rail || !dots || n < 2) return;
  const slides = Array.from(rail.children);
  dots.innerHTML = slides.map(function (_, i) {
    return '<button class="cdot' + (!i ? ' cdot--on' : '') + '" data-i="' + i + '" aria-label="Slide ' + (i + 1) + '"></button>';
  }).join('');
  function cur() { return Math.round(rail.scrollLeft / Math.max(1, (slides[0] ? slides[0].offsetWidth + 12 : 1))); }
  function go(i) {
    i = Math.max(0, Math.min(slides.length - 1, i));
    slides[i].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
    dots.querySelectorAll('.cdot').forEach(function (d, j) { d.classList.toggle('cdot--on', j === i); });
  }
  el.querySelector('#carousel-prev').onclick = function () { go(cur() - 1); };
  el.querySelector('#carousel-next').onclick = function () { go(cur() + 1); };
  dots.onclick = function (e) { var d = e.target.closest('[data-i]'); if (d) go(+d.dataset.i); };
  rail.addEventListener('scroll', function () {
    var c = cur();
    dots.querySelectorAll('.cdot').forEach(function (d, j) { d.classList.toggle('cdot--on', j === c); });
  }, { passive: true });
}

function _homeCard(target, label, value, sub) {
  return '<button type="button" class="stat-card stat-card--link" data-go="' + esc(target) + '">'
    + '<div class="stat-card__label">' + esc(label) + '</div>'
    + '<div class="stat-card__value">' + esc(value) + '</div>'
    + '<div class="stat-card__sub">' + esc(sub) + '</div></button>';
}

registerView('home', 'Home', loadHomeView);
