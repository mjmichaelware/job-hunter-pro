/* views/render_jobs.js — read-only saved-jobs browser. SAFE: opens from
   /api/batches (free). No discovery here — that lives in the Discovery view.
   Toolbar = Filters (sheet) · layout toggle · group-by · sort. */

// Stable identity for a job: exact source URL only. Distinct openings that
// share a title/company are NOT collapsed. Falls back to title|company|location
// solely when a job has no URL at all.
function _jobUniqueKey(j) {
  const url = String(pick(j, ['source_url', 'url', 'share_link', 'apply_url', 'job_id'], '') || '').trim().toLowerCase();
  if (url) return url;
  return [
    pick(j, ['title'], ''),
    pick(j, ['company', 'company_name'], ''),
    pick(j, ['location', 'resolved_address'], '')
  ].join('|').toLowerCase();
}

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
  // Deduplicate on exact source URL only. EVERY distinct opening is kept as
  // its own card — no title collapsing, no count rollups, no truncation.
  results.forEach(function (res) {
    const batch = res && res.batch ? res.batch : null;
    if (!batch) return;
    arr(batch, ['accepted', 'data', 'jobs']).forEach(function (j) {
      const key = 'A|' + _jobUniqueKey(j);
      if (seen.has(key)) return; seen.add(key);
      jobs.push(j);
    });
    arr(batch, ['rejected']).forEach(function (j) {
      const key = 'R|' + _jobUniqueKey(j);
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

  let html = '<div class="toolbar"><p class="status-line">' + esc(_jobsState.msg) + '</p>'
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
    html += '<p class="state-empty">No saved jobs yet. Open <b>Discovery</b> to run the first search.</p>';
  } else {
    console.debug('[UI_RENDER] jobs view rendering', accepted.length, 'accepted +', unresolved.length, 'unresolved');
    html += section('Accepted', accepted, false) + section('Needs resolution', unresolved, true);
    if (!accepted.length && !unresolved.length) html += '<p class="state-empty">No jobs match the current filters.</p>';
  }
  if (AppState.activeView !== 'jobs') return; // stale view, user navigated away
  el.innerHTML = html;
  wireBentoCards(el, accepted.concat(unresolved));
  wireJobsToolbar(el);
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
  el.querySelectorAll('.chip__x').forEach(function (x) {
    x.addEventListener('click', function () { delete AppState.filters[x.dataset.chip]; renderJobsView(); });
  });
}

async function loadJobsView() {
  const el = mount();
  if (el) el.innerHTML = '<p class="state-loading">Loading saved jobs (free, no quota)…</p>';
  const indData = await safeFetch('/api/industries');
  _jobsState.industries = arr(indData, ['industries']);

  if (AppState.liveResult) {                      // came from a Discovery run
    // Combine accepted and rejected into a single master collection, then
    // dedupe on exact URL only. Every distinct opening is displayed.
    const combined = (AppState.liveResult.jobs || []).concat(AppState.liveResult.rejected || []);
    const seenLive = new Set();
    _jobsState.jobs = combined.filter(function (j) {
      const k = _jobUniqueKey(j);
      if (seenLive.has(k)) return false;
      seenLive.add(k);
      return true;
    });
    _jobsState.rejected = [];
    _jobsState.msg = AppState.liveResult.msg + ' · live result';
    AppState.liveResult = null;
  } else {
    const r = await loadJobsFromBatches();
    _jobsState.jobs = r.jobs; _jobsState.rejected = r.rejected;
    _jobsState.msg = (r.source === 'none')
      ? 'No saved batches yet.'
      : (r.jobs.length + ' accepted · ' + r.rejected.length + ' need resolution · ' + (r.batchCount || '?') + ' batches' + (r.cached ? ' · cached (offline)' : ' · free'));
  }

  // Default filters: all blank => show everything. No filter ever narrows the
  // feed unless the user explicitly opens the filter sheet and applies one.
  AppState.filters = {
    industry: '',
    min_core: '',
    min_role_fit: '',
    max_transit: '',
    max_radius: '',
    q: '',
    posted_within: ''
  };

  renderJobsView();
  hydratePendingJobs(0);
}

// Progressive info-card hydration: ask the server to enrich up to 10
// not-yet-enriched jobs, merge results back, re-render, repeat a few rounds.
// Uses reasoning providers (OpenAI/Gemini/Groq/xAI) + bounded source/web
// research — no discovery quota is spent.
let _hydrating = false;
async function hydratePendingJobs(round) {
  if (_hydrating || round >= 3) return;
  const pending = _jobsState.jobs.filter(function (j) { return !j.ai_enriched && !j._hydrate_attempted; });
  if (!pending.length) return;
  _hydrating = true;
  const batch = pending.slice(0, 10);
  batch.forEach(function (j) { j._hydrate_attempted = true; });
  try {
    const res = await fetch('/api/hydrate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jobs: batch, limit: batch.length }),
    });
    if (res.ok) {
      const payload = await res.json();
      const hydrated = (payload && payload.data) || [];
      const index = {};
      _jobsState.jobs.forEach(function (j, i) { index[_jobUniqueKey(j)] = i; });
      hydrated.forEach(function (h) {
        const idx = index[_jobUniqueKey(h)];
        if (idx != null) _jobsState.jobs[idx] = h;
      });
      if (AppState.activeView === 'jobs') renderJobsView();
    }
  } catch (err) {
    console.warn('[hydrate] failed:', err && err.message);
  }
  _hydrating = false;
  hydratePendingJobs(round + 1);
}

registerView('jobs', 'Jobs', loadJobsView);
