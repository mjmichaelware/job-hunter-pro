/* views/render_opportunities.js — Company radar built from real batch data.
   Google Places is disabled; this view aggregates hiring companies from
   discovered batches instead. No fake data. */

async function loadOpportunitiesView() {
  const el = mount(); if (!el) return;
  el.innerHTML = '<p class="state-loading">Building company radar…</p>';

  const [batchList, provData] = await Promise.all([
    safeFetch('/api/batches'),
    safeFetch('/api/providers'),
  ]);

  const batches = arr(batchList, ['batches']).slice(0, 3);  // 3 most recent
  const companyMap = {};

  // Aggregate jobs from recent batches by company
  for (const b of batches) {
    const bId = b.id || b;
    try {
      const snap = await safeFetch('/api/batches/' + encodeURIComponent(bId));
      const jobs = arr(snap, ['data', 'jobs', 'accepted', 'results']);
      for (const j of jobs) {
        const co = (cleanText(j.company || j.company_name || j.restaurant_name, '')).trim();
        if (!co) continue;
        if (!companyMap[co]) {
          companyMap[co] = { name: co, count: 0, sources: new Set(), roles: [], industry: '', address: '', lastSeen: b.created_at || b };
        }
        const c = companyMap[co];
        c.count++;
        const src = j.source || j._provider || j.via || '';
        if (src) c.sources.add(src);
        const role = cleanText(j.title || j.job_title, '');
        if (role && c.roles.length < 4 && c.roles.indexOf(role) < 0) c.roles.push(role);
        const ind = cleanText(j.industry, '') || (Array.isArray(j.tags) && j.tags.length ? cleanText(j.tags[0], '') : '');
        if (ind && !c.industry) c.industry = ind;
        const addr = cleanText(j.resolved_address || j.location, '');
        if (addr && !c.address) c.address = addr;
      }
    } catch (e) {}
  }

  const companies = Object.values(companyMap).sort(function (a, b) { return b.count - a.count; });

  let html = sectionHeader({
    icon: 'opportunities', kicker: 'Local radar',
    title: 'Company radar',
    blurb: 'Employers actively hiring across your recent discovery batches, ranked by open roles found. Tap Research to vet any company before you apply.',
  });

  if (!companies.length) {
    html += emptyArt({ icon: 'opportunities', title: 'Radar is empty',
      body: 'Run a discovery and the companies hiring near you will surface here, ranked by how many roles they posted.',
      action: { label: 'Open Discovery', go: 'discovery' } });
  } else {
    html += '<div class="opp-list stagger-in">'
      + companies.slice(0, 40).map(function (c) {
          const srcs = Array.from(c.sources).join(', ');
          const initials = c.name.split(' ').slice(0, 2).map(function (w) { return w[0] || ''; }).join('').toUpperCase();
          const mapsQ = encodeURIComponent(c.address ? (c.name + ' ' + c.address) : c.name);
          const roleHint = c.roles.length ? c.roles.slice(0, 3).join(', ') : '';
          return '<div class="opp-card">'
            + '<div class="opp-card__avatar" aria-hidden="true">' + esc(initials) + '</div>'
            + '<div class="opp-card__info">'
            + '<div class="opp-card__name">' + esc(c.name) + '</div>'
            + '<div class="opp-card__meta">'
            + '<span class="badge badge-cached">' + c.count + ' role' + (c.count === 1 ? '' : 's') + '</span>'
            + (c.industry ? ' <span class="tag">' + esc(c.industry) + '</span>' : '')
            + (srcs ? ' <span class="tag">' + esc(srcs) + '</span>' : '')
            + '</div>'
            + (roleHint ? '<div class="opp-card__roles">' + esc(roleHint) + '</div>' : '')
            + '</div>'
            + '<div class="opp-card__actions">'
            + '<a class="btn-link" href="https://www.google.com/search?q=' + encodeURIComponent(c.name + ' jobs hiring') + '" target="_blank" rel="noopener noreferrer">Research ↗</a>'
            + '<a class="btn-link" href="https://www.google.com/maps/search/?api=1&query=' + mapsQ + '" target="_blank" rel="noopener noreferrer">Map ↗</a>'
            + '</div>'
            + '</div>';
        }).join('')
      + '</div>';
    if (companies.length > 40) html += '<p class="status-line">Showing top 40 of ' + companies.length + ' companies.</p>';
  }

  // Active provider list at bottom
  const providers = provData ? (provData.providers || []) : [];
  const avail = Array.isArray(providers) ? providers.filter(function (p) { return p.is_available === true || p.status === 'ready'; }) : [];
  if (avail.length) {
    html += '<h2 class="section-heading">Active discovery sources</h2>'
      + '<div class="card-row">'
      + avail.slice(0, 8).map(function (p) {
          return '<div class="stat-card"><div class="stat-card__label">' + esc(p.label || p.key || '') + '</div>'
            + '<div class="stat-card__value"><span class="badge badge-safe">live</span></div></div>';
        }).join('')
      + '</div>';
  }

  el.innerHTML = html;
  wireGo(el);
  JHP_SYNC.remember('opportunities', { companies: companies });
}

registerView('opportunities', 'Opportunities', loadOpportunitiesView);
