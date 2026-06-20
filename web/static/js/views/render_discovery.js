/* views/render_discovery.js — Discovery launcher. The only place that triggers
   live provider calls. Two clean actions: browse saved (free) + fresh run. */

async function loadDiscoveryView() {
  const el = mount(); if (!el) return;

  // Load provider count safely before rendering
  const provData = await safeFetch('/api/providers');
  const providers = provData ? (provData.providers || provData.available || []) : [];
  const liveCount = Array.isArray(providers)
    ? providers.filter(function (p) { return p.available || p.status === 'available'; }).length
    : (typeof providers === 'object' ? Object.values(providers).filter(function (p) { return p.available; }).length : 0);

  const countLabel = liveCount ? (liveCount + ' provider' + (liveCount === 1 ? '' : 's') + ' active') : 'Providers loading…';

  el.innerHTML = '<section class="discovery">'
    + sectionHeader({
        icon: 'discovery', kicker: 'Discovery engine',
        title: 'Run a search',
        blurb: 'Fan-out across ' + countLabel + ' simultaneously. Results are deduplicated, place-resolved, scored, and stored for free offline browsing. Opening this page spends nothing.',
      })
    + '<div class="discovery__actions">'
    + '<button type="button" id="disc-reload" class="btn btn-glow">'
    + '<span class="btn__label">' + esc(t('jobs.reload')) + '</span>'
    + '<span class="spinner" hidden></span></button>'
    + '<button type="button" id="disc-local" class="btn btn-glow">'
    + '<span class="btn__label">📍 Local jobs near 84115</span>'
    + '<span class="spinner" hidden></span></button>'
    + '<button type="button" id="disc-run" class="btn btn-glow btn-warn">'
    + '<span class="btn__label">' + esc(t('jobs.run')) + '</span>'
    + '<span class="spinner" hidden></span></button>'
    + '</div>'
    + '<label class="disc-toggle"><input type="checkbox" id="disc-dedup" checked> '
    + 'Remove duplicate listings (same role from multiple sources)</label>'
    + '<p class="status-line" id="disc-status">' + esc(t('disc.idle')) + '</p>'
    + '<div class="disc-tips">'
    + '<div class="disc-tip"><span class="disc-tip__icon">💾</span><strong>Browse saved</strong> — instant, free. Shows jobs from the last stored batch.</div>'
    + '<div class="disc-tip"><span class="disc-tip__icon">⚡</span><strong>Fresh discovery</strong> — queries all active providers simultaneously. Results are stored for offline access.</div>'
    + '</div>'
    + '</section>';

  const status = el.querySelector('#disc-status');
  const reload = el.querySelector('#disc-reload');
  const run = el.querySelector('#disc-run');
  const local = el.querySelector('#disc-local');

  async function runDiscovery(btn, mode, label) {
    if (!confirm(t('jobs.confirm'))) return;
    busy(btn, true);
    status.textContent = 'Scanning ' + label + ' across ' + countLabel + '…';
    if (typeof announce === 'function') announce(label + ' discovery started');
    // Energize the ambient field while a real run is in flight (honest: it only
    // surges because discovery is actually running right now).
    if (typeof updateVolumetric === 'function') updateVolumetric({ intensity: 1 });
    const dedupEl = el.querySelector('#disc-dedup');
    const opts = Object.assign({}, AppState.filters, mode ? { mode: mode } : {});
    if (dedupEl && !dedupEl.checked) opts.dedup = 0;
    const data = await fetchJobsLive(opts);
    if (typeof updateVolumetric === 'function') updateVolumetric({ intensity: 0.55 });
    busy(btn, false);
    if (!data) { status.textContent = 'Discovery failed or timed out. Check Debug tab for details.'; return; }
    const jobs = arr(data, ['data', 'jobs', 'accepted', 'results']);
    const rejected = arr(data, ['rejected']);
    const raw = data.raw_count != null ? data.raw_count : (jobs.length + rejected.length);
    const stored = data.stored ? 'saved' : 'not saved (storage error)';
    const msg = jobs.length + ' accepted · ' + raw + ' raw · ' + rejected.length + ' flagged · ' + stored;
    AppState.liveResult = { jobs: jobs, rejected: rejected, msg: msg };
    status.textContent = msg + ' — opening Jobs…';
    if (typeof announce === 'function') announce(msg);
    navigate('jobs');
  }

  reload.addEventListener('click', async function () {
    busy(reload, true);
    const list = await safeFetch('/api/batches');
    const n = arr(list, ['batches']).length;
    busy(reload, false);
    status.textContent = n ? (n + ' batch' + (n === 1 ? '' : 'es') + ' available — opening Jobs…') : 'No saved batches yet. Run fresh discovery first.';
    if (typeof announce === 'function') announce(status.textContent);
    if (n) { AppState.liveResult = null; navigate('jobs'); }
  });

  if (local) local.addEventListener('click', function () { runDiscovery(local, 'local', 'local jobs near 84115'); });
  run.addEventListener('click', function () { runDiscovery(run, '', 'all jobs'); });

  function busy(btn, on) {
    btn.disabled = on;
    const sp = btn.querySelector('.spinner');
    if (sp) sp.hidden = !on;
  }
}

registerView('discovery', 'Discovery', loadDiscoveryView);
