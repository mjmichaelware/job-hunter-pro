/* Live Jobs renderer.
 *
 * Single job: show EVERY job the backend returns. The backend /api/jobs (live)
 * returns hundreds of real jobs in `data` (plus `rejected` unresolved candidates).
 * This renderer must never hide them behind a dry-run gate or a silent filter.
 *
 * Quota note: a live run costs at most MAX_SERP_QUERIES (4) SerpAPI searches —
 * the bulk of results come from The Muse (free/keyless). The result is cached for
 * the browser session so switching tabs does not re-spend.
 */

function normalizeJobsPayload(payload) {
  if (!payload || typeof payload !== 'object') return [];
  if (Array.isArray(payload.data)) return payload.data;
  if (Array.isArray(payload.jobs)) return payload.jobs;
  if (Array.isArray(payload.accepted)) return payload.accepted;
  if (Array.isArray(payload.results)) return payload.results;
  if (payload.data && Array.isArray(payload.data.jobs)) return payload.data.jobs;
  return [];
}

function normalizeRejectedPayload(payload) {
  if (!payload || typeof payload !== 'object') return [];
  if (Array.isArray(payload.rejected)) return payload.rejected;
  if (payload.data && Array.isArray(payload.data.rejected)) return payload.data.rejected;
  return [];
}

function pickJobField(job, keys, fallback = '') {
  for (const key of keys) {
    const value = job?.[key];
    if (value !== undefined && value !== null && value !== '') return value;
  }
  return fallback;
}

function jobNumber(value, fallback = null) {
  if (value === undefined || value === null || value === '') return fallback;
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function safeJobHref(value) {
  const raw = String(value || '').trim();
  if (!raw) return '';
  if (raw.startsWith('http://') || raw.startsWith('https://')) return raw;
  return '';
}

function renderProviderBreakdown(data) {
  const breakdown = data?.provider_breakdown || {};
  const keys = Object.keys(breakdown);
  if (!keys.length) return '';

  return `
    <div class="card" style="margin-bottom:var(--space-md);">
      <h3>Provider Fan-Out</h3>
      <p class="muted">Search providers that participated in this live run.</p>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:var(--space-sm);">
        ${keys.map((key) => {
          const info = breakdown[key] || {};
          const status = info.status || (info.available ? 'ok' : 'dormant');
          const rawCount = info.raw_count ?? 0;
          const attempted = info.queries_attempted ?? 0;
          const badge = rawCount > 0 ? 'badge-safe' : (info.available ? 'badge-cached' : 'badge-budget-guarded');
          return `<span class="badge ${badge}">${escapeHtml(key)}: ${escapeHtml(rawCount)} raw / ${escapeHtml(attempted)} q / ${escapeHtml(status)}</span>`;
        }).join('')}
      </div>
    </div>`;
}

/*
 * loadJobs — defaults to LIVE. This is the whole point of the tab: show the jobs.
 * Pass { live:false } only for an explicit safe dry-run preview.
 * Pass { forceRefresh:true } to bypass the session cache and re-run discovery.
 */
async function loadJobs(options = {}) {
  const { live = true, forceRefresh = false } = options || {};
  const container = document.getElementById('jobs-container');
  if (!container) return;

  // Reuse the cached live result on repeat tab visits (no re-spend).
  const cached = AppState.cachedData.jobs;
  if (!forceRefresh && live && cached && !cached.dry_run && normalizeJobsPayload(cached).length) {
    renderJobsList(cached, { live: true });
    return;
  }

  container.innerHTML = live
    ? '<div class="chart-fallback">Running live discovery — The Muse (free) plus active paid providers within budget. One moment…</div>'
    : '<div class="chart-fallback">Safe dry-run: this preview does not spend discovery provider budget.</div>';

  const data = live ? await fetchJobsLive() : await fetchJobsDryRun();

  AppState.cachedData.jobs = data;
  renderJobsList(data, { live });
}

function renderJobsList(data, options = {}) {
  const { live = true } = options || {};
  const container = document.getElementById('jobs-container');
  if (!container) return;

  if (!data) {
    container.innerHTML = '<div class="chart-fallback">Could not reach the jobs service. Check your connection and try Run Live Discovery again.</div>';
    return;
  }

  // A dry-run preview carries no jobs — say so plainly, do not pretend it failed.
  if (data.dry_run) {
    container.innerHTML = `
      <div class="card">
        <h3>Safe dry-run only</h3>
        <p class="muted">${escapeHtml(data.message || 'No discovery provider budget was spent.')}</p>
        <p style="margin-top:var(--space-sm);">Press <strong>Run Live Discovery</strong> to fetch real jobs.</p>
      </div>`;
    return;
  }

  const accepted = normalizeJobsPayload(data);
  const rejected = normalizeRejectedPayload(data);

  // Optional client-side narrowing — only when the user EXPLICITLY set a filter.
  // Unknown/blank fields never hide a job. Default state shows everything.
  const filterRadius = jobNumber(AppState.filters?.radius, null);
  const filterMatch = jobNumber(AppState.filters?.matchScore, null);
  const filterIndustry = (AppState.filters?.industry || '').trim();
  const hasRadius = filterRadius !== null && filterRadius > 0;
  const hasMatch = filterMatch !== null && filterMatch > 0;

  const filtered = accepted.filter((job) => {
    const industry = pickJobField(job, ['industry', 'industry_key'], '');
    const radius = jobNumber(pickJobField(job, ['haversine_radius_miles', 'radius_miles', 'distance_miles'], null), null);
    const match = jobNumber(pickJobField(job, ['match_score', 'score', 'resonance_score', 'match'], null), null);
    if (filterIndustry && industry && industry !== filterIndustry) return false;
    if (hasRadius && radius !== null && radius > filterRadius) return false;
    if (hasMatch && match !== null && match < filterMatch) return false;
    return true;
  });

  const acceptedCount = data.count ?? data.accepted_count ?? accepted.length;
  const rawCount = data.raw_count ?? (accepted.length + rejected.length);
  const rejectedCount = data.rejected_count ?? rejected.length;
  const narrowed = filtered.length !== accepted.length;

  if (!accepted.length && !rejected.length) {
    container.innerHTML = '<div class="chart-fallback">Live discovery returned no job candidates from the active providers.</div>';
    return;
  }

  container.innerHTML = `
    ${renderProviderBreakdown(data)}
    <div class="card" style="margin-bottom:var(--space-md);">
      <h3>${escapeHtml(acceptedCount)} live jobs</h3>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:var(--space-sm);">
        <span class="badge badge-safe">Showing: ${escapeHtml(filtered.length)}</span>
        ${narrowed ? `<span class="badge badge-budget-guarded">${escapeHtml(acceptedCount - filtered.length)} hidden by filters</span>` : ''}
        <span class="badge badge-budget-guarded">Needs resolution: ${escapeHtml(rejectedCount)}</span>
        <span class="badge badge-cached">Raw scanned: ${escapeHtml(rawCount)}</span>
        <span class="badge badge-cached">Queries: ${escapeHtml(data.query_count ?? '—')}</span>
      </div>
      ${narrowed ? '<p class="muted" style="margin-top:var(--space-sm);">Filters are narrowing the list. Press <strong>Show All / Reset</strong> to see every job.</p>' : ''}
    </div>

    ${filtered.length ? `
      <section style="margin-bottom:var(--space-lg);">
        ${filtered.map(renderAcceptedJobCard).join('')}
      </section>
    ` : `
      <div class="chart-fallback">No jobs match the filters you set. Press <strong>Show All / Reset</strong>.</div>
    `}

    ${rejected.length ? `
      <section style="margin-top:var(--space-lg);">
        <h3 style="margin-bottom:var(--space-sm);">Unresolved live candidates</h3>
        <p class="muted" style="margin-bottom:var(--space-md);">
          Real provider results whose address/place could not be auto-resolved. Shown so nothing is silently dropped.
        </p>
        ${renderRejectionSummary(data)}
        ${rejected.map(renderUnresolvedCandidateCard).join('')}
      </section>
    ` : ''}
  `;
}

function renderRejectionSummary(data) {
  const summary = data?.rejection_summary || {};
  const entries = Object.entries(summary);
  if (!entries.length) return '';

  return `
    <div class="card" style="margin-bottom:var(--space-md);border-color:var(--warning);">
      <h4>Why candidates need resolution</h4>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:var(--space-sm);">
        ${entries.map(([reason, count]) => `<span class="badge badge-budget-guarded">${escapeHtml(reason)} × ${escapeHtml(count)}</span>`).join('')}
      </div>
    </div>`;
}

function renderAcceptedJobCard(job) {
  const title = escapeHtml(pickJobField(job, ['title', 'job_title', 'name'], 'Untitled role'));
  const company = escapeHtml(pickJobField(job, ['company', 'company_name', 'employer', 'place_name'], 'Company unavailable'));
  const address = escapeHtml(pickJobField(job, ['normalized_address', 'resolved_address', 'address', 'location', 'detected_location'], 'Location not resolved'));
  const source = escapeHtml(pickJobField(job, ['source', 'provider', 'source_provider_id', 'via', '_provider'], 'source'));
  const salary = escapeHtml(pickJobField(job, ['salary', 'salary_hint', 'pay', 'compensation'], ''));

  const match = jobNumber(pickJobField(job, ['match_score', 'score', 'resonance_score', 'match'], null), null);
  const transitSeconds = jobNumber(pickJobField(job, ['commute_matrix_seconds', 'transit_seconds', 'commute_seconds'], null), null);
  const radius = jobNumber(pickJobField(job, ['haversine_radius_miles', 'radius_miles', 'distance_miles'], null), null);
  const url = safeJobHref(pickJobField(job, ['source_url', 'url', 'apply_url', 'share_link'], ''));

  const tags = [
    pickJobField(job, ['role_family'], ''),
    pickJobField(job, ['industry'], ''),
  ].filter(Boolean).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('');

  const distanceCopy = radius !== null ? `${radius.toFixed(1)} mi` : 'Distance not resolved';
  const commuteCopy = transitSeconds !== null ? `${Math.round(transitSeconds / 60)} min transit` : '';
  const scoreCopy = match !== null ? `${Math.round(match)}% match` : source;

  return `
    <article class="job-card card" style="margin-bottom: var(--space-md);">
      <div style="display:flex; justify-content:space-between; gap:var(--space-md); align-items:flex-start;">
        <div>
          <h3>${title}</h3>
          <p class="muted">${company}</p>
          <p class="muted">${address}${distanceCopy ? ` · ${distanceCopy}` : ''}${commuteCopy ? ` · ${commuteCopy}` : ''}</p>
        </div>
        <span class="badge badge-safe">${escapeHtml(scoreCopy)}</span>
      </div>
      ${salary ? `<p style="margin-top:var(--space-sm); color:var(--success); font-weight:700;">${salary}</p>` : ''}
      <div style="margin-top:var(--space-sm); display:flex; flex-wrap:wrap; gap:6px;">
        <span class="badge badge-cached">source: ${source}</span>
        ${tags}
      </div>
      ${url ? `<p style="margin-top:var(--space-sm);"><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Open / Apply</a></p>` : ''}
    </article>`;
}

function renderUnresolvedCandidateCard(item) {
  const title = escapeHtml(pickJobField(item, ['title', 'job_title', 'name'], 'Untitled live candidate'));
  const company = escapeHtml(pickJobField(item, ['company', 'company_name', 'restaurant_name', 'employer'], 'Company unavailable'));
  const address = escapeHtml(pickJobField(item, ['resolved_address', 'normalized_address', 'address', 'location'], 'No exact address resolved'));
  const provider = escapeHtml(pickJobField(item, ['provider', 'source', '_provider'], 'provider'));
  const url = safeJobHref(pickJobField(item, ['source_url', 'url', 'apply_url', 'share_link'], ''));
  const reasons = Array.isArray(item?.reasons) ? item.reasons
    : Array.isArray(item?.resolution_flags) ? item.resolution_flags : [];

  return `
    <article class="job-card card" style="margin-bottom:var(--space-md);border-color:var(--warning);">
      <div style="display:flex;justify-content:space-between;gap:var(--space-md);align-items:flex-start;">
        <div>
          <h3>${title}</h3>
          <p class="muted">${company}</p>
          <p class="muted">${address}</p>
        </div>
        <span class="badge badge-budget-guarded">Needs resolution</span>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:var(--space-sm);">
        <span class="badge badge-cached">provider: ${provider}</span>
        ${reasons.map(reason => `<span class="badge badge-budget-guarded">${escapeHtml(reason)}</span>`).join('')}
      </div>
      ${url ? `<p style="margin-top:var(--space-sm);"><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Open / Apply</a></p>` : ''}
    </article>`;
}
