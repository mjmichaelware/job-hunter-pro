/* views/render_discovery.js — Discovery launcher. The only place that triggers
   live provider calls. Two clean actions: browse saved (free) + fresh run. */

async function loadDiscoveryView() {
  const el = mount(); if (!el) return;

  // Load provider count safely before rendering
  const provData = await safeFetch('/api/providers');
  const providers = provData ? (provData.providers || provData.available || []) : [];
  const liveProviders = Array.isArray(providers)
    ? providers.filter(function (p) { return p.available || p.status === 'available'; })
    : Object.values(providers).filter(function (p) { return p.available; });
  const liveCount = liveProviders.length;
  const countLabel = liveCount ? (liveCount + ' provider' + (liveCount === 1 ? '' : 's') + ' active') : 'Providers loading…';

  el.innerHTML = '<section class="discovery">'
    + sectionHeader({
        icon: 'discovery', kicker: 'Discovery engine',
        title: 'Run a search',
        blurb: 'Fan-out across ' + countLabel + ' simultaneously. Results are deduplicated, place-resolved, scored, and stored for free offline browsing. Opening this page spends nothing.',
      })
    + '<div class="discovery__actions">'
    + '<button type="button" id="disc-reload" class="btn btn-glow"><span class="btn__label">' + esc(t('jobs.reload')) + '</span><span class="spinner" hidden></span></button>'
    + '<button type="button" id="disc-local" class="btn btn-glow"><span class="btn__label">📍 Local jobs near 84115</span><span class="spinner" hidden></span></button>'
    + '<button type="button" id="disc-run" class="btn btn-glow btn-warn"><span class="btn__label">' + esc(t('jobs.run')) + '</span><span class="spinner" hidden></span></button>'
    + '</div>'
    + '<label class="disc-toggle"><input type="checkbox" id="disc-dedup" checked> Remove duplicate listings (same role from multiple sources)</label>'
    + '<p class="status-line" id="disc-status">' + esc(t('disc.idle')) + '</p>'
    + '<pre class="disc-log" id="disc-log" hidden></pre>'
    + '<div class="disc-tips">'
    + '<div class="disc-tip"><span class="disc-tip__icon">💾</span><strong>Browse saved</strong> — instant, free. Shows jobs from the last stored batch.</div>'
    + '<div class="disc-tip"><span class="disc-tip__icon">⚡</span><strong>Fresh discovery</strong> — queries all active providers simultaneously. Results are stored for offline access.</div>'
    + '</div></section>';

  const status = el.querySelector('#disc-status');
  const log = el.querySelector('#disc-log');
  const reload = el.querySelector('#disc-reload');
  const run = el.querySelector('#disc-run');
  const local = el.querySelector('#disc-local');

  function logLine(msg) {
    log.hidden = false;
    log.textContent += msg + '\n';
    log.scrollTop = log.scrollHeight;
  }

  async function runDiscovery(btn, mode, label) {
    if (!confirm(t('jobs.confirm'))) return;
    busy(btn, true);
    log.textContent = '';
    log.hidden = false;
    logLine('▶ Starting ' + label + ' — ' + countLabel);
    if (liveProviders.length) logLine('  Providers: ' + liveProviders.slice(0, 8).map(function (p) { return p.label || p.key; }).join(', ') + (liveProviders.length > 8 ? ' + ' + (liveProviders.length - 8) + ' more…' : ''));
    logLine('  Running concurrently — this may take 30–120 s…');
    status.textContent = 'Scanning ' + label + ' across ' + countLabel + '…';
    if (typeof announce === 'function') announce(label + ' discovery started');
    if (typeof updateVolumetric === 'function') updateVolumetric({ intensity: 1 });

    const t0 = Date.now();
    const ticker = setInterval(function () { status.textContent = 'Still scanning… ' + Math.round((Date.now() - t0) / 1000) + 's elapsed'; }, 2000);

    const dedupEl = el.querySelector('#disc-dedup');
    const opts = Object.assign({}, AppState.filters, mode ? { mode: mode } : {});
    if (dedupEl && !dedupEl.checked) opts.dedup = 0;
    const data = await fetchJobsLive(opts);

    clearInterval(ticker);
    if (typeof updateVolumetric === 'function') updateVolumetric({ intensity: 0.55 });
    busy(btn, false);
    if (!data) { status.textContent = 'Discovery failed or timed out. Check Debug tab for details.'; logLine('✗ Failed or timed out.'); return; }

    const jobs = arr(data, ['data', 'jobs', 'accepted', 'results']);
    const rejected = arr(data, ['rejected']);
    const raw = data.raw_count != null ? data.raw_count : (jobs.length + rejected.length);
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
    const stored = data.stored ? 'saved to history' : 'storage error';
    logLine('✓ Done in ' + elapsed + 's');
    logLine('  Raw fetched : ' + raw);
    logLine('  Accepted    : ' + jobs.length);
    logLine('  Flagged     : ' + rejected.length);
    logLine('  Storage     : ' + stored);
    if (data.enriched_count != null) logLine('  Enriched    : ' + data.enriched_count + ' jobs (Maps + AI)');
    if (data.enrich_cap != null) logLine('  Enrich cap  : ' + data.enrich_cap);
    const msg = jobs.length + ' accepted · ' + raw + ' raw · ' + rejected.length + ' flagged · ' + stored;
    AppState.liveResult = { jobs: jobs, rejected: rejected, msg: msg };
    status.textContent = msg;
    if (typeof announce === 'function') announce(msg);
    setTimeout(function () { navigate('jobs'); }, 1800);
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

  function busy(btn, on) { btn.disabled = on; var sp = btn.querySelector('.spinner'); if (sp) sp.hidden = !on; }
}

registerView('discovery', 'Discovery', loadDiscoveryView);
