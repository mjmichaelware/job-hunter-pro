/* views/render_discovery.js — the ONLY place that can spend provider budget.
   Two glassy actions: reload saved (free) and run fresh discovery (explicit
   confirm). Forward-wired: sends whatever is in AppState.filters (origin,
   posted_within, sort, …) so new params activate automatically once backend honors them. */

function loadDiscoveryView() {
  const el = mount(); if (!el) return;
  el.innerHTML = '<section class="discovery">'
    + '<div class="info-box"><strong>' + esc(t('disc.safe_title')) + '</strong> ' + esc(t('disc.safe')) + '</div>'
    + '<div class="discovery__actions">'
    + '<button type="button" id="disc-reload" class="btn btn-glow"><span class="btn__label">' + esc(t('jobs.reload')) + '</span><span class="spinner" hidden></span></button>'
    + '<button type="button" id="disc-run" class="btn btn-glow btn-warn"><span class="btn__label">' + esc(t('jobs.run')) + '</span><span class="spinner" hidden></span></button>'
    + '</div>'
    + '<p class="status-line" id="disc-status">' + esc(t('disc.idle')) + '</p>'
    + '</section>';

  const status = el.querySelector('#disc-status');
  const reload = el.querySelector('#disc-reload');
  const run = el.querySelector('#disc-run');

  reload.addEventListener('click', async function () {
    busy(reload, true);
    const list = await safeFetch('/api/batches');
    const n = arr(list, ['batches']).length;
    busy(reload, false);
    status.textContent = n ? (n + ' saved batches available — opening Jobs…') : 'No saved batches yet.';
    if (typeof announce === 'function') announce(status.textContent);
    if (n) { AppState.liveResult = null; navigate('jobs'); }
  });

  run.addEventListener('click', async function () {
    if (!confirm(t('jobs.confirm'))) return;
    busy(run, true);
    status.textContent = 'Running fresh discovery across all providers — may take a minute…';
    if (typeof announce === 'function') announce('Live discovery started');
    const data = await fetchJobsLive(AppState.filters);   // forward-wired query params
    busy(run, false);
    if (!data) { status.textContent = 'Discovery failed or timed out. Try again.'; return; }
    const jobs = arr(data, ['data', 'jobs', 'accepted', 'results']);
    const rejected = arr(data, ['rejected']);
    const raw = data.raw_count != null ? data.raw_count : (jobs.length + rejected.length);
    const stored = data.stored ? 'saved' : 'NOT saved (storage error)';
    const msg = jobs.length + ' accepted · ' + raw + ' raw · ' + rejected.length + ' need resolution · ' + stored;
    AppState.liveResult = { jobs: jobs, rejected: rejected, msg: msg };
    status.textContent = msg + ' — opening Jobs…';
    if (typeof announce === 'function') announce(msg);
    navigate('jobs');
  });

  function busy(btn, on) {
    btn.disabled = on;
    const sp = btn.querySelector('.spinner');
    if (sp) sp.hidden = !on;
  }
}

registerView('discovery', 'Discovery', loadDiscoveryView);
