/* views/render_jobs.js — Jobs view. SAFE BOOT: opens from saved batches only.
   Live discovery fires ONLY on the explicit "Run fresh discovery" button + confirm.
   This is the exact behavior that fixed "jobs not showing" — do not change it. */

async function loadJobsFromBatches() {
  const list = await safeFetch('/api/batches');
  let batches = arr(list, ['batches']);
  if (!batches.length) {
    // offline fallback: render whatever we cached
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
      const key = [pick(j, ['source_url', 'url'], ''), pick(j, ['title'], ''), pick(j, ['company', 'company_name'], ''), pick(j, ['location', 'resolved_address'], '')].join('|');
      if (seen.has(key)) return; seen.add(key); jobs.push(j);
    });
    arr(batch, ['rejected']).forEach(function (j) {
      const key = 'R|' + [pick(j, ['source_url', 'url'], ''), pick(j, ['title'], ''), pick(j, ['company', 'company_name'], '')].join('|');
      if (seen.has(key)) return; seen.add(key); rejected.push(j);
    });
  });
  const out = { jobs: jobs, rejected: rejected, batchCount: batches.length, source: 'saved' };
  JHP_SYNC.remember('jobs', out);
  return out;
}

function renderJobsView(jobs, rejected, statusMsg, industries) {
  const el = mount(); if (!el) return;
  const f = AppState.filters;
  const shownAccepted = applyLocalFilters(jobs, f);
  const shownRejected = applyLocalFilters(rejected, f);

  let html = '<div class="toolbar"><p class="status-line">' + esc(statusMsg) + '</p>'
    + '<div class="toolbar-actions">'
    + '<button type="button" id="btn-reload-saved" class="btn">' + esc(t('jobs.reload')) + '</button>'
    + '<button type="button" id="btn-run-live" class="btn btn-warn">' + esc(t('jobs.run')) + '</button>'
    + '</div></div>'
    + renderChips(f) + renderFilters(f, industries, jobs.concat(rejected));

  if (!jobs.length && !rejected.length) {
    html += '<p class="state-empty">No saved jobs yet. Press "' + esc(t('jobs.run')) + '" to build the first batch.</p>';
  } else {
    if (shownAccepted.length) html += '<h2 class="section-heading">Accepted (' + shownAccepted.length + ')</h2><div class="job-list bento-grid bento-grid--jobs">' + shownAccepted.map(function (j) { return bentoJobCard(j, false); }).join('') + '</div>';
    if (shownRejected.length) html += '<h2 class="section-heading">Needs resolution (' + shownRejected.length + ')</h2><div class="job-list bento-grid bento-grid--jobs">' + shownRejected.map(function (j) { return bentoJobCard(j, true); }).join('') + '</div>';
    if (!shownAccepted.length && !shownRejected.length) html += '<p class="state-empty">No jobs match the current filters.</p>';
  }
  el.innerHTML = html;
  wireBentoCards(el, shownAccepted.concat(shownRejected));
  wireJobsControls(el, jobs, rejected, industries);
}

function wireJobsControls(el, jobs, rejected, industries) {
  el.querySelector('#btn-reload-saved').addEventListener('click', function () { loadJobsView(); });
  const clearBtn = el.querySelector('#btn-clear-filters');
  if (clearBtn) clearBtn.addEventListener('click', function () { AppState.filters = {}; loadJobsView(); });
  const applyBtn = el.querySelector('#btn-apply-filters');
  if (applyBtn) applyBtn.addEventListener('click', function () { AppState.filters = readFilters(el); renderJobsView(jobs, rejected, jobs.length + ' accepted · filtered locally', industries); });
  el.querySelectorAll('.chip__x').forEach(function (x) { x.addEventListener('click', function () { delete AppState.filters[x.dataset.chip]; renderJobsView(jobs, rejected, jobs.length + ' accepted · filtered locally', industries); }); });
  el.querySelector('#btn-run-live').addEventListener('click', function () { runLiveDiscovery(el, industries); });
}

async function runLiveDiscovery(el, industries) {
  if (!confirm(t('jobs.confirm'))) return;
  const status = el.querySelector('.status-line');
  if (status) status.textContent = 'Running fresh discovery across all providers — may take a minute…';
  el.querySelector('#btn-run-live').disabled = true;
  if (typeof announce === 'function') announce('Live discovery started');
  const data = await fetchJobsLive(AppState.filters);
  if (!data) { if (status) status.textContent = 'Discovery failed or timed out. Try again.'; el.querySelector('#btn-run-live').disabled = false; return; }
  const liveJobs = arr(data, ['data', 'jobs', 'accepted', 'results']);
  const liveRej = arr(data, ['rejected']);
  const raw = data.raw_count != null ? data.raw_count : (liveJobs.length + liveRej.length);
  const stored = data.stored ? 'saved' : 'NOT saved (storage error)';
  const msg = liveJobs.length + ' accepted · ' + raw + ' raw · ' + liveRej.length + ' need resolution · ' + stored;
  if (typeof announce === 'function') announce(msg);
  renderJobsView(liveJobs, liveRej, msg, industries);
}

async function loadJobsView() {
  const el = mount();
  if (el) el.innerHTML = '<p class="state-loading">Loading saved jobs (free, no quota)…</p>';
  const indData = await safeFetch('/api/industries');
  const industries = arr(indData, ['industries']);
  const r = await loadJobsFromBatches();
  let msg;
  if (r.source === 'none') msg = 'No saved batches yet. Press "' + t('jobs.run') + '" to build the first batch.';
  else msg = r.jobs.length + ' accepted · ' + r.rejected.length + ' need resolution · ' + (r.batchCount || '?') + ' batches'
    + (r.cached ? ' · cached (offline)' : ' · free, no quota spent');
  renderJobsView(r.jobs, r.rejected, msg, industries);
}

registerView('jobs', 'Jobs', loadJobsView);
