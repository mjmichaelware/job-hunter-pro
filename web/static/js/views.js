/* views.js — one render function per view. All data comes from real API calls.
   No demo arrays, no placeholder rows, no hardcoded companies/counts. */

// ─── shared helpers ──────────────────────────────────────────────────────────

function mount() {
  return document.getElementById('view-mount');
}

function renderState(cls, msg) {
  const el = mount();
  if (el) el.innerHTML = '<p class="' + esc(cls) + '">' + esc(msg) + '</p>';
}

function formatMins(seconds) {
  if (seconds == null || seconds === '') return 'unavailable';
  const m = Math.round(Number(seconds) / 60);
  return m + ' min';
}

function formatMiles(miles) {
  if (miles == null || miles === '') return 'unavailable';
  return Number(miles).toFixed(1) + ' mi';
}

function tagList(items) {
  if (!Array.isArray(items) || !items.length) return '';
  return items.map(t => '<span class="tag">' + esc(t) + '</span>').join(' ');
}

function evidenceRow(label, value) {
  const display = (value === null || value === undefined || value === '') ? '<span class="na">unavailable</span>' : esc(String(value));
  return '<tr><th>' + esc(label) + '</th><td>' + display + '</td></tr>';
}

// Build an evidence panel for a job object
function buildEvidenceHtml(job) {
  const raw = esc(pick(job, ['raw_title', 'title'], ''));
  const norm = esc(pick(job, ['title', 'job_title'], ''));
  const trackId = esc(pick(job, ['source_url', 'url', 'id'], raw + '|' + esc(pick(job, ['company', 'company_name'], ''))));

  return '<div class="evidence-panel">'
    + '<h3>Evidence</h3>'
    + '<table class="evidence-table">'
    + evidenceRow('Raw title', pick(job, ['raw_title'], null))
    + evidenceRow('Normalized title', pick(job, ['title', 'job_title'], null))
    + evidenceRow('Company', pick(job, ['company', 'company_name', 'restaurant_name'], null))
    + evidenceRow('Place ID', pick(job, ['place_id'], null))
    + evidenceRow('Resolved address', pick(job, ['resolved_address', 'normalized_address', 'location'], null))
    + evidenceRow('Source provider', pick(job, ['source', '_provider', 'provider', 'via'], null))
    + evidenceRow('Source URL', pick(job, ['source_url', 'url'], null))
    + evidenceRow('Commute', job.commute_seconds != null ? formatMins(job.commute_seconds) : null)
    + evidenceRow('Radius', job.radius_miles != null ? formatMiles(job.radius_miles) : null)
    + evidenceRow('Match score', pick(job, ['match', 'match_score'], null))
    + evidenceRow('Review score', pick(job, ['review_score'], null))
    + evidenceRow('Consistency score', pick(job, ['consistency_score'], null))
    + evidenceRow('Risk level', pick(job, ['risk_level'], null))
    + evidenceRow('Google rating', pick(job, ['google_rating'], null))
    + evidenceRow('Google reviews', pick(job, ['google_review_count'], null))
    + evidenceRow('Role family', pick(job, ['role_family'], null))
    + evidenceRow('Tags', Array.isArray(job.tags) ? job.tags.join(', ') : null)
    + evidenceRow('Resolution flags', Array.isArray(job.resolution_flags) ? job.resolution_flags.join(', ') : null)
    + evidenceRow('Needs resolution', job.needs_resolution != null ? String(job.needs_resolution) : null)
    + '</table>'
    + '<button type="button" class="btn-track" data-job-id="' + esc(trackId) + '">Track this job</button>'
    + '</div>';
}

// Render a single job card (accepted or unresolved)
function jobCard(job, isUnresolved) {
  const title = esc(pick(job, ['title', 'job_title', 'name'], 'Untitled role'));
  const company = esc(pick(job, ['company', 'company_name', 'restaurant_name', 'employer', 'place_name'], 'Company not listed'));
  const location = esc(pick(job, ['resolved_address', 'normalized_address', 'location', 'listing_location', 'detected_location'], 'Location not resolved'));
  const source = esc(pick(job, ['source', '_provider', 'provider', 'via'], ''));
  const url = href(pick(job, ['source_url', 'url', 'apply_url', 'share_link'], ''));
  const flags = []
    .concat(Array.isArray(job.resolution_flags) ? job.resolution_flags : [])
    .concat(Array.isArray(job.reasons) ? job.reasons : []);

  const matchVal = pick(job, ['match', 'match_score'], null);
  const matchDisp = matchVal != null ? '<span class="badge badge-safe">match ' + esc(String(matchVal)) + '</span>' : '';
  const reviewVal = pick(job, ['review_score'], null);
  const reviewDisp = reviewVal != null ? '<span class="badge badge-cached">review ' + esc(String(reviewVal)) + '</span>' : '';
  const cardCls = 'job-card' + (isUnresolved ? ' job-card--unresolved' : '');
  const uid = 'ev-' + Math.random().toString(36).slice(2, 9);

  return '<div class="' + cardCls + '">'
    + '<div class="job-card__head">'
    + '<div class="job-card__title">' + title + '</div>'
    + '<div class="job-card__badges">' + matchDisp + reviewDisp + '</div>'
    + '</div>'
    + '<div class="job-card__meta">' + company + ' &middot; ' + location
    + (source ? ' &middot; <span class="source-chip">' + source + '</span>' : '') + '</div>'
    + (flags.length ? '<div class="job-card__flags">' + tagList(flags) + '</div>' : '')
    + (url ? '<div class="job-card__actions"><a href="' + esc(url) + '" target="_blank" rel="noopener" class="btn-link">Open / Apply</a></div>' : '')
    + '<button type="button" class="btn-evidence" data-uid="' + uid + '">Show evidence</button>'
    + '<div id="' + uid + '" class="evidence-wrapper" hidden>' + buildEvidenceHtml(job) + '</div>'
    + '</div>';
}

// Wire evidence toggles and track buttons in a container
function wireJobCards(container) {
  container.querySelectorAll('.btn-evidence').forEach(btn => {
    btn.addEventListener('click', () => {
      const uid = btn.dataset.uid;
      const panel = document.getElementById(uid);
      if (!panel) return;
      const hidden = panel.hidden;
      panel.hidden = !hidden;
      btn.textContent = hidden ? 'Hide evidence' : 'Show evidence';
    });
  });
  container.querySelectorAll('.btn-track').forEach(btn => {
    btn.addEventListener('click', async () => {
      const jobId = btn.dataset.jobId;
      if (!jobId) return;
      btn.disabled = true;
      btn.textContent = 'Tracking…';
      try {
        const res = await fetch('/api/applications', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_id: jobId, status: 'DISCOVERED', notes: '' }),
        });
        if (res.ok || res.status === 409) {
          btn.textContent = res.status === 409 ? 'Already tracked' : 'Tracked';
        } else {
          btn.textContent = 'Track failed';
          btn.disabled = false;
        }
      } catch (e) {
        btn.textContent = 'Track failed';
        btn.disabled = false;
      }
    });
  });
}

// ─── VIEW: Jobs ──────────────────────────────────────────────────────────────

async function loadJobsFromBatches() {
  const list = await safeFetch('/api/batches');
  let batches = arr(list, ['batches']);
  if (!batches.length) return { jobs: [], rejected: [], source: 'none' };

  batches.sort((a, b) => String(b.object_name || '').localeCompare(String(a.object_name || '')));
  batches = batches.slice(0, 30);

  const results = await Promise.all(
    batches.map(b => safeFetch('/api/batch/' + b.object_name))
  );

  const seen = new Set();
  const jobs = [];
  const rejected = [];
  for (const res of results) {
    const batch = res && res.batch ? res.batch : null;
    if (!batch) continue;
    for (const j of arr(batch, ['accepted', 'data', 'jobs'])) {
      const key = [pick(j, ['source_url', 'url'], ''), pick(j, ['title'], ''),
                   pick(j, ['company', 'company_name'], ''), pick(j, ['location', 'resolved_address'], '')].join('|');
      if (seen.has(key)) continue;
      seen.add(key);
      jobs.push(j);
    }
    for (const j of arr(batch, ['rejected'])) {
      const key = 'R|' + [pick(j, ['source_url', 'url'], ''), pick(j, ['title'], ''), pick(j, ['company', 'company_name'], '')].join('|');
      if (seen.has(key)) continue;
      seen.add(key);
      rejected.push(j);
    }
  }
  return { jobs, rejected, batchCount: batches.length, source: 'saved' };
}

function renderJobsView(jobs, rejected, statusMsg, filters, industryOptions) {
  const el = mount();
  if (!el) return;

  const industryOpts = (industryOptions || []).map(ind =>
    '<option value="' + esc(ind.key) + '">' + esc(ind.label) + '</option>'
  ).join('');

  const fv = filters || {};

  let html = '<div class="view-jobs">'
    + '<div class="toolbar">'
    + '<p class="status-line">' + esc(statusMsg) + '</p>'
    + '<div class="toolbar-actions">'
    + '<button type="button" id="btn-reload-saved" class="btn">Reload saved (free)</button>'
    + '<button type="button" id="btn-run-live" class="btn btn-warn">Run fresh discovery (spends quota)</button>'
    + '</div>'
    + '</div>'

    + '<details class="filter-panel"><summary>Filters (local only — no quota spent)</summary>'
    + '<div class="filter-grid">'
    + '<label>Industry<select id="f-industry"><option value="">All</option>' + industryOpts + '</select></label>'
    + '<label>Min rating<input type="number" id="f-min-rating" min="0" max="5" step="0.1" value="' + esc(fv.min_rating || '') + '" placeholder="0.0"></label>'
    + '<label>Max radius (mi)<input type="number" id="f-max-radius" min="0" max="50" step="0.5" value="' + esc(fv.max_radius || '') + '" placeholder="any"></label>'
    + '<label>Max transit (min)<input type="number" id="f-max-transit" min="0" max="120" value="' + esc(fv.max_transit || '') + '" placeholder="any"></label>'
    + '<label>Min match score<input type="number" id="f-min-match" min="0" max="100" value="' + esc(fv.min_match || '') + '" placeholder="0"></label>'
    + '<label>Role / keyword<input type="text" id="f-q" value="' + esc(fv.q || '') + '" placeholder="cook, server…"></label>'
    + '</div>'
    + '<div class="filter-actions">'
    + '<button type="button" id="btn-apply-filters" class="btn">Apply filters (re-fetches live)</button>'
    + '<button type="button" id="btn-clear-filters" class="btn">Clear</button>'
    + '</div>'
    + '</details>';

  if (!jobs.length && !rejected.length) {
    html += '<p class="state-empty">No saved jobs yet. Press "Run fresh discovery" to build the first batch.</p>';
  } else {
    if (jobs.length) {
      html += '<h2 class="section-heading">Accepted (' + jobs.length + ')</h2>'
        + '<div class="job-list">' + jobs.map(j => jobCard(j, false)).join('') + '</div>';
    }
    if (rejected.length) {
      html += '<h2 class="section-heading">Needs resolution (' + rejected.length + ')</h2>'
        + '<div class="job-list">' + rejected.map(j => jobCard(j, true)).join('') + '</div>';
    }
  }

  html += '</div>';
  el.innerHTML = html;
  wireJobCards(el);

  el.querySelector('#btn-reload-saved').addEventListener('click', () => loadJobsView());
  el.querySelector('#btn-clear-filters').addEventListener('click', () => {
    AppState.filters = {};
    loadJobsView();
  });
  el.querySelector('#btn-run-live').addEventListener('click', async () => {
    if (!confirm('Run fresh discovery? This may spend SerpAPI / provider quota.')) return;
    const statusEl = el.querySelector('.status-line');
    if (statusEl) statusEl.textContent = 'Running fresh discovery across all providers — may take a minute…';
    el.querySelector('#btn-run-live').disabled = true;
    try {
      const data = await fetchJobsLive(AppState.filters);
      if (!data) {
        if (statusEl) statusEl.textContent = 'Discovery failed or timed out. Try again.';
        el.querySelector('#btn-run-live').disabled = false;
        return;
      }
      const liveJobs = arr(data, ['data', 'jobs', 'accepted', 'results']);
      const liveRejected = arr(data, ['rejected']);
      const raw = data.raw_count != null ? data.raw_count : (liveJobs.length + liveRejected.length);
      const stored = data.stored ? 'saved' : 'NOT saved (storage error)';
      const provBd = data.provider_breakdown || {};
      const provSummary = Object.entries(provBd).map(([k, v]) => k + ':' + (v.raw_count || 0)).join(' | ');
      const msg = liveJobs.length + ' accepted · ' + raw + ' raw · ' + liveRejected.length + ' need resolution · ' + stored
        + (provSummary ? ' | providers: ' + provSummary : '');
      // Re-render with live results
      const indData = await safeFetch('/api/industries');
      const indOpts = arr(indData, ['industries']);
      renderJobsView(liveJobs, liveRejected, msg, AppState.filters, indOpts);
    } catch (err) {
      if (el.querySelector('.status-line')) el.querySelector('.status-line').textContent = 'Error: ' + err.message;
      if (el.querySelector('#btn-run-live')) el.querySelector('#btn-run-live').disabled = false;
    }
  });
  el.querySelector('#btn-apply-filters').addEventListener('click', async () => {
    const f = {
      industry: el.querySelector('#f-industry').value,
      min_rating: el.querySelector('#f-min-rating').value,
      max_radius: el.querySelector('#f-max-radius').value,
      max_transit: el.querySelector('#f-max-transit').value,
      min_match: el.querySelector('#f-min-match').value,
      q: el.querySelector('#f-q').value,
    };
    AppState.filters = f;
    // Apply filters locally first (no quota), then optionally re-fetch
    loadJobsView();
  });
}

async function loadJobsView() {
  const el = mount();
  if (el) el.innerHTML = '<p class="state-loading">Loading saved jobs (free, no quota)…</p>';

  const indData = await safeFetch('/api/industries');
  const industryOptions = arr(indData, ['industries']);

  const { jobs, rejected, batchCount, source } = await loadJobsFromBatches();

  let msg;
  if (source === 'none') {
    msg = 'No saved batches yet. Press "Run fresh discovery" to build the first batch.';
  } else {
    msg = jobs.length + ' unique accepted · ' + rejected.length + ' need resolution · across ' + batchCount + ' saved batches · free, no quota spent';
  }
  renderJobsView(jobs, rejected, msg, AppState.filters, industryOptions);
}

registerView('jobs', 'Jobs', loadJobsView);

// ─── VIEW: Providers ─────────────────────────────────────────────────────────

async function loadProvidersView() {
  const data = await safeFetch('/api/providers');
  const el = mount();
  if (!el) return;

  if (!data) {
    el.innerHTML = '<p class="state-error">Could not load providers.</p>';
    return;
  }

  const providers = arr(data, ['providers']);
  if (!providers.length) {
    el.innerHTML = '<p class="state-empty">No providers registered.</p>';
    return;
  }

  const discovery = providers.filter(p => p.type === 'discovery' || p.type === 'search');
  const reasoning = providers.filter(p => p.type === 'reasoning' || p.type === 'llm');
  const other = providers.filter(p => !discovery.includes(p) && !reasoning.includes(p));

  function provRow(p) {
    const statusCls = p.status === 'ready' ? 'badge-safe'
      : p.status === 'dormant' ? 'badge-disabled'
      : p.status === 'disabled_by_policy' ? 'badge-error'
      : 'badge-disabled';
    const keyNote = p.requires_api_key ? (p.is_available ? '' : ' — key missing') : ' — no key needed';
    const reason = p.reason ? '<span class="na"> (' + esc(p.reason) + ')</span>' : '';
    return '<tr>'
      + '<td>' + esc(p.label || p.key) + '</td>'
      + '<td><span class="badge ' + statusCls + '">' + esc(p.status || 'unknown') + '</span></td>'
      + '<td>' + esc(p.description || '') + keyNote + reason + '</td>'
      + '</tr>';
  }

  function provTable(list, heading, note) {
    if (!list.length) return '';
    return '<h2 class="section-heading">' + esc(heading) + '</h2>'
      + (note ? '<p class="section-note">' + esc(note) + '</p>' : '')
      + '<table class="data-table"><thead><tr><th>Provider</th><th>Status</th><th>Notes</th></tr></thead>'
      + '<tbody>' + list.map(provRow).join('') + '</tbody></table>';
  }

  el.innerHTML = '<div class="view-providers">'
    + provTable(discovery, 'Discovery providers', 'These providers retrieve real job listings.')
    + provTable(reasoning, 'Reasoning providers', 'Reasoning only — these LLMs classify, extract, and score. They are never used for job discovery.')
    + provTable(other, 'Other providers', '')
    + '</div>';
}

registerView('providers', 'Providers', loadProvidersView);

// ─── VIEW: Budget ─────────────────────────────────────────────────────────────

async function loadBudgetView() {
  const data = await safeFetch('/api/usage');
  const el = mount();
  if (!el) return;

  if (!data) {
    el.innerHTML = '<p class="state-error">Could not load usage data.</p>';
    return;
  }

  const serp = data.serpapi || {};
  const budget = data.budget || {};
  const storage = data.storage || {};

  const left = serp.total_searches_left;
  const leftCls = left == null ? 'badge-disabled'
    : left > 100 ? 'badge-safe'
    : left > 40 ? 'badge-warn'
    : 'badge-error';

  let html = '<div class="view-budget">'
    + '<div class="card-row">'

    + '<div class="stat-card">'
    + '<div class="stat-card__label">SerpAPI searches left</div>'
    + '<div class="stat-card__value"><span class="badge ' + leftCls + '">'
    + (left != null ? esc(String(left)) : 'unavailable') + '</span></div>'
    + '</div>'

    + '<div class="stat-card">'
    + '<div class="stat-card__label">Plan</div>'
    + '<div class="stat-card__value">' + esc(serp.plan_name || 'unavailable') + '</div>'
    + '</div>'

    + '<div class="stat-card">'
    + '<div class="stat-card__label">This month used</div>'
    + '<div class="stat-card__value">' + (serp.this_month_usage != null ? esc(String(serp.this_month_usage)) : 'unavailable') + '</div>'
    + '</div>'

    + '<div class="stat-card">'
    + '<div class="stat-card__label">Searches per month</div>'
    + '<div class="stat-card__value">' + (serp.searches_per_month != null ? esc(String(serp.searches_per_month)) : 'unavailable') + '</div>'
    + '</div>'

    + '</div>'  // card-row

    + '<h2 class="section-heading">Budget guard</h2>'
    + '<table class="data-table"><tbody>'
    + '<tr><th>Min searches left guard</th><td>' + esc(String(budget.min_searches_left_guard || 'unavailable')) + '</td></tr>'
    + '<tr><th>Max SerpAPI queries per live run</th><td>' + esc(String(budget.max_serp_queries_per_live_run || budget.max_queries || 'unavailable')) + '</td></tr>'
    + '<tr><th>Max raw jobs per live run</th><td>' + esc(String(budget.max_raw_jobs_per_live_run || budget.max_raw_jobs || 'unavailable')) + '</td></tr>'
    + '</tbody></table>'

    + '<h2 class="section-heading">Storage</h2>'
    + '<table class="data-table"><tbody>'
    + Object.entries(storage).map(([k, v]) => '<tr><th>' + esc(k) + '</th><td>' + esc(String(v)) + '</td></tr>').join('')
    + (Object.keys(storage).length === 0 ? '<tr><td colspan="2" class="na">No storage info returned.</td></tr>' : '')
    + '</tbody></table>'

    + '<div class="info-box">'
    + '<strong>Safe by default:</strong> Opening this dashboard does not run live discovery and costs nothing. '
    + 'The "Run fresh discovery" button in the Jobs view is the only action that may spend quota.'
    + '</div>'
    + '</div>';

  el.innerHTML = html;
}

registerView('budget', 'Budget', loadBudgetView);

// ─── VIEW: History ────────────────────────────────────────────────────────────

async function loadHistoryView() {
  const data = await safeFetch('/api/history?hours=168');
  const el = mount();
  if (!el) return;

  if (!data) {
    el.innerHTML = '<p class="state-error">Could not load history.</p>';
    return;
  }

  const batches = arr(data, ['batches']);

  let html = '<div class="view-history">';

  if (data.batch_count != null || data.job_count != null) {
    html += '<div class="card-row">'
      + (data.batch_count != null ? '<div class="stat-card"><div class="stat-card__label">Total batches</div><div class="stat-card__value">' + esc(String(data.batch_count)) + '</div></div>' : '')
      + (data.job_count != null ? '<div class="stat-card"><div class="stat-card__label">Total jobs stored</div><div class="stat-card__value">' + esc(String(data.job_count)) + '</div></div>' : '')
      + '</div>';
  }

  if (!batches.length) {
    html += '<p class="state-empty">No batch history exists yet. Run a discovery to create the first batch.</p>';
  } else {
    html += '<table class="data-table">'
      + '<thead><tr><th>Batch</th><th>Created</th><th>Accepted</th><th>Rejected</th><th>Raw</th><th>Queries</th></tr></thead>'
      + '<tbody>';
    for (const b of batches) {
      const counts = b.counts || {};
      const ts = b.created_at_utc || b.updated || b.object_name || 'unknown';
      const name = b.object_name || b.batch_id || '—';
      html += '<tr>'
        + '<td><code class="batch-id">' + esc(name) + '</code></td>'
        + '<td>' + esc(ts) + '</td>'
        + '<td>' + (counts.accepted != null ? esc(String(counts.accepted)) : '—') + '</td>'
        + '<td>' + (counts.rejected != null ? esc(String(counts.rejected)) : '—') + '</td>'
        + '<td>' + (counts.raw != null ? esc(String(counts.raw)) : '—') + '</td>'
        + '<td>' + (counts.queries != null ? esc(String(counts.queries)) : '—') + '</td>'
        + '</tr>';
    }
    html += '</tbody></table>';
  }

  html += '</div>';
  el.innerHTML = html;
}

registerView('history', 'History', loadHistoryView);

// ─── VIEW: Opportunities ──────────────────────────────────────────────────────

async function loadOpportunitiesView() {
  const data = await safeFetch('/api/opportunities');
  const el = mount();
  if (!el) return;

  if (!data) {
    el.innerHTML = '<p class="state-error">Could not load opportunities.</p>';
    return;
  }

  let html = '<div class="view-opportunities">';

  if (data.enabled === false || data.status === 'disabled') {
    html += '<div class="info-box info-box--warn"><strong>Opportunities disabled:</strong> '
      + esc(data.message || 'This feature is not enabled in the current configuration.')
      + '</div>';
    el.innerHTML = html + '</div>';
    return;
  }

  const opps = arr(data, ['data', 'opportunities']);

  if (data.count != null) {
    html += '<p class="status-line">' + esc(String(data.count)) + ' opportunities returned.</p>';
  }

  if (!opps.length) {
    html += '<p class="state-empty">No opportunities returned. The feature may need configuration or a location origin.</p>';
  } else {
    html += '<div class="opp-list">';
    for (const o of opps) {
      const name = esc(pick(o, ['name', 'place_name'], 'Unnamed'));
      const addr = esc(pick(o, ['resolved_address', 'address', 'vicinity'], 'Address unavailable'));
      const rating = pick(o, ['google_rating', 'rating'], null);
      const radius = pick(o, ['radius_miles'], null);
      const commute = pick(o, ['commute_seconds'], null);
      html += '<div class="opp-card">'
        + '<div class="opp-card__name">' + name + '</div>'
        + '<div class="opp-card__addr">' + addr + '</div>'
        + '<div class="opp-card__meta">'
        + (rating != null ? '<span class="badge badge-safe">rating ' + esc(String(rating)) + '</span> ' : '<span class="na">rating unavailable</span> ')
        + (radius != null ? '<span class="tag">' + formatMiles(radius) + '</span> ' : '')
        + (commute != null ? '<span class="tag">' + formatMins(commute) + ' transit</span>' : '')
        + '</div>'
        + '</div>';
    }
    html += '</div>';
  }

  html += '</div>';
  el.innerHTML = html;
}

registerView('opportunities', 'Opportunities', loadOpportunitiesView);

// ─── VIEW: Applications ───────────────────────────────────────────────────────

async function loadApplicationsView() {
  const data = await safeFetch('/api/applications');
  const el = mount();
  if (!el) return;

  if (!data) {
    el.innerHTML = '<p class="state-error">Could not load applications.</p>';
    return;
  }

  const apps = arr(data, ['applications']);

  const STATUSES = ['DISCOVERED', 'APPLIED', 'INTERVIEWING', 'OFFERED', 'REJECTED', 'WITHDRAWN'];

  let html = '<div class="view-applications">';

  if (!apps.length) {
    html += '<p class="state-empty">No tracked applications yet. Open a job card and press "Track this job" to start tracking.</p>';
  } else {
    html += '<table class="data-table">'
      + '<thead><tr><th>Job ID</th><th>Status</th><th>Notes</th><th>Created</th><th>Updated</th><th>Change status</th></tr></thead>'
      + '<tbody>';
    for (const a of apps) {
      const jid = esc(a.job_id || '');
      const statusCls = a.status === 'OFFERED' ? 'badge-safe'
        : a.status === 'REJECTED' ? 'badge-error'
        : a.status === 'INTERVIEWING' ? 'badge-warn'
        : 'badge-cached';
      const selectOpts = STATUSES.map(s =>
        '<option value="' + s + '"' + (s === a.status ? ' selected' : '') + '>' + s + '</option>'
      ).join('');
      html += '<tr>'
        + '<td><code>' + jid + '</code></td>'
        + '<td><span class="badge ' + statusCls + '">' + esc(a.status || 'unknown') + '</span></td>'
        + '<td>' + esc(a.notes || '') + '</td>'
        + '<td>' + esc(a.created_at || '—') + '</td>'
        + '<td>' + esc(a.updated_at || '—') + '</td>'
        + '<td><select class="status-select" data-job-id="' + jid + '">' + selectOpts + '</select>'
        + ' <button type="button" class="btn btn-sm btn-save-status" data-job-id="' + jid + '">Save</button></td>'
        + '</tr>';
    }
    html += '</tbody></table>';
  }

  html += '</div>';
  el.innerHTML = html;

  el.querySelectorAll('.btn-save-status').forEach(btn => {
    btn.addEventListener('click', async () => {
      const jid = btn.dataset.jobId;
      const sel = el.querySelector('.status-select[data-job-id="' + jid + '"]');
      if (!sel) return;
      btn.disabled = true;
      btn.textContent = 'Saving…';
      try {
        const res = await fetch('/api/applications/' + encodeURIComponent(jid), {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: sel.value }),
        });
        btn.textContent = res.ok ? 'Saved' : 'Failed';
        if (res.ok) setTimeout(() => { btn.textContent = 'Save'; btn.disabled = false; }, 1500);
        else btn.disabled = false;
      } catch (e) {
        btn.textContent = 'Error';
        btn.disabled = false;
      }
    });
  });
}

registerView('applications', 'Applications', loadApplicationsView);

// ─── VIEW: Debug ──────────────────────────────────────────────────────────────

async function loadDebugView() {
  const data = await safeFetch('/api/debug/jobs');
  const el = mount();
  if (!el) return;

  if (!data) {
    el.innerHTML = '<p class="state-error">Could not load debug data. The /api/debug/jobs endpoint may not be available.</p>';
    return;
  }

  let html = '<div class="view-debug">';

  // Counts
  const counts = { raw: data.raw_count, accepted: data.accepted_count, rejected: data.rejected_count, queries: data.query_count };
  const hasAnyCounts = Object.values(counts).some(v => v != null);
  if (hasAnyCounts) {
    html += '<div class="card-row">';
    for (const [k, v] of Object.entries(counts)) {
      html += '<div class="stat-card"><div class="stat-card__label">' + esc(k) + '</div>'
        + '<div class="stat-card__value">' + (v != null ? esc(String(v)) : '<span class="na">—</span>') + '</div></div>';
    }
    html += '</div>';
  }

  // Provider breakdown
  const pb = data.provider_breakdown || {};
  if (Object.keys(pb).length) {
    html += '<h2 class="section-heading">Provider breakdown</h2>'
      + '<table class="data-table"><thead><tr><th>Provider</th><th>Status</th><th>Raw count</th><th>Queries attempted</th><th>Cap</th></tr></thead><tbody>';
    for (const [k, v] of Object.entries(pb)) {
      html += '<tr>'
        + '<td>' + esc(v.label || k) + '</td>'
        + '<td><span class="badge ' + (v.available ? 'badge-safe' : 'badge-disabled') + '">' + esc(v.status || (v.available ? 'available' : 'unavailable')) + '</span></td>'
        + '<td>' + (v.raw_count != null ? esc(String(v.raw_count)) : '—') + '</td>'
        + '<td>' + (v.queries_attempted != null ? esc(String(v.queries_attempted)) : '—') + '</td>'
        + '<td>' + (v.cap != null ? esc(String(v.cap)) : '—') + '</td>'
        + '</tr>';
    }
    html += '</tbody></table>';
  }

  // Rejection summary
  const rs = data.rejection_summary || {};
  if (Object.keys(rs).length) {
    html += '<h2 class="section-heading">Rejection summary</h2>'
      + '<table class="data-table"><tbody>'
      + Object.entries(rs).sort((a, b) => b[1] - a[1]).map(([reason, count]) =>
          '<tr><td>' + esc(reason) + '</td><td>' + esc(String(count)) + '</td></tr>'
        ).join('')
      + '</tbody></table>';
  }

  // Resolution flag summary
  const rfs = data.resolution_flag_summary || {};
  if (Object.keys(rfs).length) {
    html += '<h2 class="section-heading">Resolution flag summary</h2>'
      + '<table class="data-table"><tbody>'
      + Object.entries(rfs).sort((a, b) => b[1] - a[1]).map(([flag, count]) =>
          '<tr><td>' + esc(flag) + '</td><td>' + esc(String(count)) + '</td></tr>'
        ).join('')
      + '</tbody></table>';
  }

  if (!hasAnyCounts && !Object.keys(pb).length && !Object.keys(rs).length) {
    html += '<p class="state-empty">No debug data available. Run a discovery batch first.</p>';
  }

  html += '</div>';
  el.innerHTML = html;
}

registerView('debug', 'Debug', loadDebugView);

// ─── VIEW: Why Three ──────────────────────────────────────────────────────────

async function loadWhyThreeView() {
  const data = await safeFetch('/api/why-three');
  const el = mount();
  if (!el) return;

  if (!data) {
    el.innerHTML = '<p class="state-error">Could not load why-three data.</p>';
    return;
  }

  let html = '<div class="view-why-three">';

  const top3 = arr(data, ['top3', 'results']);
  const msg = data.message || data.explanation || null;
  const limit = data.limit || data.min_required || null;

  if (msg) {
    html += '<div class="info-box">' + esc(msg) + '</div>';
  }

  if (!top3.length) {
    const note = limit
      ? 'The why-three engine requires at least ' + esc(String(limit)) + ' high-confidence results to rank candidates.'
      : 'No top-three results available. Run a discovery batch with enough results.';
    html += '<p class="state-empty">' + note + '</p>';
  } else {
    top3.forEach((item, i) => {
      const title = esc(pick(item, ['title', 'job_title'], 'Untitled'));
      const company = esc(pick(item, ['company', 'company_name'], 'Unknown'));
      const score = pick(item, ['resonance_score', 'match', 'match_score'], null);
      const why = pick(item, ['why_included', 'reasoning', 'explanation'], null);
      const why_not = pick(item, ['why_excluded', 'exclusions'], null);
      html += '<div class="why-card">'
        + '<div class="why-card__rank">#' + (i + 1) + '</div>'
        + '<div class="why-card__title">' + title + ' — ' + company + '</div>'
        + (score != null ? '<div class="why-card__score">Score: ' + esc(String(score)) + '</div>' : '')
        + (why ? '<div class="why-card__reason"><strong>Why included:</strong> ' + esc(why) + '</div>' : '')
        + (why_not ? '<div class="why-card__reason"><strong>Exclusions noted:</strong> ' + esc(why_not) + '</div>' : '')
        + '</div>';
    });
  }

  // Render any remaining keys as a meta table
  const knownKeys = new Set(['top3', 'results', 'message', 'explanation', 'limit', 'min_required', 'status']);
  const extra = Object.entries(data).filter(([k]) => !knownKeys.has(k));
  if (extra.length) {
    html += '<h2 class="section-heading">Additional info</h2>'
      + '<table class="data-table"><tbody>'
      + extra.map(([k, v]) => '<tr><th>' + esc(k) + '</th><td>' + esc(JSON.stringify(v)) + '</td></tr>').join('')
      + '</tbody></table>';
  }

  html += '</div>';
  el.innerHTML = html;
}

registerView('why-three', 'Why Three', loadWhyThreeView);
