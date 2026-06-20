/* views/render_jobs.js — read-only saved-jobs browser. SAFE: opens from
   /api/batches (free). No discovery here — that lives in the Discovery view.
   Toolbar = Filters (sheet) · layout toggle · group-by · sort. */

async function loadJobsFromBatches() {
  const list = await safeFetch('/api/batches');
  let batches = arr(list, ['batches']);
  if (!batches.length) {
    const cached = await JHP_SYNC.recall('jobs');
    if (cached) return Object.assign({ cached: true }, cached);
    return { jobs: [], rejected: [], source: 'none' };
  }
  batches.sort(function (a, b) { return String(b.object_name || '').localeCompare(String(a.object_name || '')); });
  batches = batches.slice(0, 30);
  const results = await Promise.all(batches.map(function (b) { return safeFetch('/api/batch/' + b.object_name); }));
  const seen = new Set(); const jobs = []; const rejected = [];
  results.forEach(function (res) {
    const batch = res && res.batch ? res.batch : null;
    if (!batch) return;
    arr(batch, ['accepted', 'data', 'jobs']).forEach(function (j) {
      const key = [pick(j, ['source_url', 'url'], ''), pick(j, ['title'], ''), pick(j, ['company', 'company_name'], '')].join('|');
      if (seen.has(key)) return; seen.add(key); jobs.push(j);
    });
    arr(batch, ['rejected']).forEach(function (j) {
      const key = 'R|' + [pick(j, ['source_url', 'url'], ''), pick(j, ['title'], '')].join('|');
      if (seen.has(key)) return; seen.add(key); rejected.push(j);
    });
  });
  const out = { jobs: jobs, rejected: rejected, batchCount: batches.length, source: 'saved' };
  JHP_SYNC.remember('jobs', out);
  return out;
}

let _jobsState = { jobs: [], rejected: [], industries: [], msg: '' };

function renderJobsView() {
  const el = mount(); if (!el) return;
  const f = AppState.filters;
  const accepted = sortJobs(applyLocalFilters(_jobsState.jobs, f), AppState.sort);
  const unresolved = sortJobs(applyLocalFilters(_jobsState.rejected, f), AppState.sort);

  let html = sectionHeader({
    icon: 'jobs', kicker: 'Live results',
    title: 'Jobs near you',
    blurb: 'Every listing is deduplicated, place-resolved, and scored. Tap a card for full evidence, or open the research links to vet the employer on Glassdoor, BBB, and Google.',
  });
  html += '<div class="toolbar"><p class="status-line">' + esc(_jobsState.msg) + '</p>'
    + '<div class="toolbar-actions">'
    + '<button type="button" id="btn-filters" class="btn btn-filter" aria-label="Open filters">⚲ Filters' + filterCountBadge(f) + '</button>'
    + renderLayoutToggle() + renderGroupControl() + renderSortControl()
    + '</div></div>' + renderChips(f);

  function section(label, list, unres) {
    if (!list.length) return '';
    const groups = groupJobs(list, AppState.groupBy);
    let s = label ? '<h2 class="section-heading">' + esc(label) + ' (' + list.length + ')</h2>' : '';
    groups.forEach(function (g) {
      if (g.label) s += '<h3 class="group-heading">' + esc(g.label) + '</h3>';
      s += '<div class="bento-grid ' + esc(AppState.layout) + '">' + g.jobs.map(function (j) { return bentoJobCard(j, unres); }).join('') + '</div>';
    });
    return s;
  }

  if (!_jobsState.jobs.length && !_jobsState.rejected.length) {
    html += emptyArt({
      icon: 'rocket', title: 'No saved jobs yet',
      body: 'Run your first discovery to fan out across every active provider. Results are stored so you can browse them here for free, even offline.',
      action: { label: 'Open Discovery', go: 'discovery' },
    });
  } else {
    html += section('Accepted', accepted, false) + section('Needs resolution', unresolved, true);
    if (!accepted.length && !unresolved.length) {
      html += emptyArt({ icon: 'filter', title: 'No jobs match these filters', body: 'Loosen the radius, match score, or keyword filters to see more results.' });
    }
  }
  el.innerHTML = html;
  applyIndustryFromJobs(_jobsState.jobs);
  if (typeof setCohort === 'function') setCohort(_jobsState.jobs.concat(_jobsState.rejected));
  wireBentoCards(el, accepted.concat(unresolved));
  wireJobsToolbar(el);
  wireGo(el);
}

function wireJobsToolbar(el) {
  const fbtn = el.querySelector('#btn-filters');
  if (fbtn) fbtn.addEventListener('click', function () { openFiltersSheet(_jobsState.industries, _jobsState.jobs.concat(_jobsState.rejected), renderJobsView); });
  el.querySelectorAll('.seg__btn[data-layout]').forEach(function (b) {
    b.addEventListener('click', function () { setLayout(b.dataset.layout); renderJobsView(); });
  });
  const gsel = el.querySelector('#group-select');
  if (gsel) gsel.addEventListener('change', function (e) { AppState.groupBy = e.target.value; renderJobsView(); });
  const ssel = el.querySelector('#sort-select');
  if (ssel) ssel.addEventListener('change', function (e) { AppState.sort = e.target.value; AppState.filters.sort = e.target.value; renderJobsView(); });
  wireChipRemove(el, renderJobsView);
}

async function loadJobsView() {
  const el = mount();
  if (el) el.innerHTML = '<p class="state-loading">Loading saved jobs (free, no quota)…</p>';
  const indData = await safeFetch('/api/industries');
  _jobsState.industries = arr(indData, ['industries']);

  if (AppState.liveResult) {                      // came from a Discovery run
    _jobsState.jobs = AppState.liveResult.jobs;
    _jobsState.rejected = AppState.liveResult.rejected;
    _jobsState.msg = AppState.liveResult.msg + ' · live result';
    AppState.liveResult = null;
  } else {
    const r = await loadJobsFromBatches();
    _jobsState.jobs = r.jobs; _jobsState.rejected = r.rejected;
    _jobsState.msg = (r.source === 'none')
      ? 'No saved batches yet.'
      : (r.jobs.length + ' accepted · ' + r.rejected.length + ' need resolution · ' + (r.batchCount || '?') + ' batches' + (r.cached ? ' · cached (offline)' : ' · free'));
  }
  renderJobsView();
}

registerView('jobs', 'Jobs', loadJobsView);
