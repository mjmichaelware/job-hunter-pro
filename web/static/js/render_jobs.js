function normalizeJobsPayload(payload) {
  if (!payload || typeof payload !== 'object') return [];
  if (Array.isArray(payload.jobs)) return payload.jobs;
  if (Array.isArray(payload.data)) return payload.data;
  if (payload.data && Array.isArray(payload.data.jobs)) return payload.data.jobs;
  if (Array.isArray(payload.results)) return payload.results;
  if (Array.isArray(payload.accepted)) return payload.accepted;
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

async function loadJobs(options = {}) {
  const { live = false } = options || {};
  const container = document.getElementById('jobs-container');
  if (!container) return;

  container.innerHTML = live
    ? '<div class="chart-fallback">Running live discovery. This may use discovery provider budget.</div>'
    : '<div class="chart-fallback">Checking safe dry-run status. Opening this dashboard does not run live discovery.</div>';

  const url = live ? API_URLS.jobs : `${API_URLS.jobs}?dry_run=1`;
  const data = await safeFetch(url);

  AppState.cachedData.jobs = data;
  renderJobsList(data, { live });
}

function renderJobsList(data, options = {}) {
  const { live = false } = options || {};
  const container = document.getElementById('jobs-container');
  if (!container) return;

  const accepted = normalizeJobsPayload(data);
  const rejected = normalizeRejectedPayload(data);

  if (data?.dry_run) {
    container.innerHTML = `
      <div class="chart-fallback">
        <strong>Live jobs are not loaded yet.</strong><br>
        ${escapeHtml(data.message || 'Dry run completed without spending discovery provider budget.')}<br>
        Use <strong>Run Live Discovery</strong> when ready to spend provider budget.
      </div>`;
    return;
  }

  const filteredAccepted = accepted.filter((job) => {
    const industry = pickJobField(job, ['industry', 'industry_key'], '');
    const radius = jobNumber(pickJobField(job, ['haversine_radius_miles', 'radius_miles', 'distance_miles'], null), null);
    const match = jobNumber(pickJobField(job, ['match_score', 'score', 'resonance_score', 'match'], null), null);

    if (AppState.filters?.industry && industry && industry !== AppState.filters.industry) return false;
    if (radius !== null && AppState.filters?.radius && radius > Number(AppState.filters.radius)) return false;
    if (match !== null && AppState.filters?.matchScore && match < Number(AppState.filters.matchScore)) return false;
    return true;
  });

  if (!filteredAccepted.length && !rejected.length) {
    container.innerHTML = live
      ? '<div class="chart-fallback">Live discovery returned no job candidates from the active providers.</div>'
      : '<div class="chart-fallback">No live jobs loaded. Run live discovery when ready to spend provider budget.</div>';
    return;
  }

  const rawCount = data?.raw_count ?? (filteredAccepted.length + rejected.length);
  const acceptedCount = data?.count ?? filteredAccepted.length;
  const rejectedCount = data?.rejected_count ?? rejected.length;

  container.innerHTML = `
    ${renderProviderBreakdown(data)}
    <div class="card" style="margin-bottom:var(--space-md);">
      <h3>All Live Job Candidates</h3>
      <p class="muted">
        Showing accepted verified jobs plus unresolved candidates. Unresolved candidates are real provider results,
        but they still need address/place resolution before commute/radius scoring is trusted.
      </p>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:var(--space-sm);">
        <span class="badge badge-safe">Accepted: ${escapeHtml(acceptedCount)}</span>
        <span class="badge badge-budget-guarded">Needs resolution: ${escapeHtml(rejectedCount)}</span>
        <span class="badge badge-cached">Raw scanned: ${escapeHtml(rawCount)}</span>
        <span class="badge badge-cached">Queries: ${escapeHtml(data?.query_count ?? '—')}</span>
      </div>
    </div>

    ${filteredAccepted.length ? `
      <section style="margin-bottom:var(--space-lg);">
        <h3 style="margin-bottom:var(--space-sm);">Verified accepted jobs</h3>
        ${filteredAccepted.map(renderAcceptedJobCard).join('')}
      </section>
    ` : `
      <div class="chart-fallback">No verified accepted jobs passed the strict address/radius/transit rules in this run.</div>
    `}

    ${rejected.length ? `
      <section style="margin-top:var(--space-lg);">
        <h3 style="margin-bottom:var(--space-sm);">Unresolved live candidates</h3>
        <p class="muted" style="margin-bottom:var(--space-md);">
          These are still real live job candidates. They were previously hidden because address/place resolution failed
          or strict commute/radius rules could not be verified.
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
  const address = escapeHtml(pickJobField(job, ['normalized_address', 'resolved_address', 'address', 'location', 'detected_location'], 'Address unresolved'));
  const source = escapeHtml(pickJobField(job, ['source', 'provider', 'source_provider_id', 'via'], 'source unavailable'));
  const salary = escapeHtml(pickJobField(job, ['salary', 'salary_hint', 'pay', 'compensation'], 'Salary not listed'));

  const match = jobNumber(pickJobField(job, ['match_score', 'score', 'resonance_score', 'match'], null), null);
  const review = jobNumber(pickJobField(job, ['review_score', 'review_heuristic_score'], null), null);
  const rating = jobNumber(pickJobField(job, ['rating', 'place_rating', 'google_rating'], null), null);
  const reviews = jobNumber(pickJobField(job, ['review_count', 'place_review_count', 'google_review_count'], null), null);
  const transitSeconds = jobNumber(pickJobField(job, ['commute_matrix_seconds', 'transit_seconds', 'commute_seconds'], null), null);
  const radius = jobNumber(pickJobField(job, ['haversine_radius_miles', 'radius_miles', 'distance_miles'], null), null);
  const url = safeJobHref(pickJobField(job, ['source_url', 'url', 'apply_url'], ''));

  const tags = [
    pickJobField(job, ['role_family'], ''),
    pickJobField(job, ['industry'], ''),
    source ? `source: ${source}` : ''
  ].filter(Boolean).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('');

  const commuteCopy = transitSeconds !== null ? `${Math.round(transitSeconds / 60)} min transit` : 'Transit unavailable';
  const distanceCopy = radius !== null ? `${radius.toFixed(1)} mi` : 'Distance unavailable';
  const scoreCopy = match !== null ? `${Math.round(match)}% match` : 'Verified candidate';
  const reviewCopy = [
    rating !== null ? `${rating.toFixed(1)}★` : null,
    reviews !== null ? `${reviews} reviews` : null,
    review !== null ? `Review score ${Math.round(review)}` : null
  ].filter(Boolean).join(' · ') || 'Review intelligence unavailable';

  return `
    <article class="job-card card" style="margin-bottom: var(--space-md);">
      <div style="display:flex; justify-content:space-between; gap:var(--space-md); align-items:flex-start;">
        <div>
          <h3>${title}</h3>
          <p class="muted">${company}</p>
          <p class="muted">${address} · ${distanceCopy} · ${commuteCopy}</p>
        </div>
        <span class="badge badge-safe">${escapeHtml(scoreCopy)}</span>
      </div>
      <p style="margin-top:var(--space-sm);">${reviewCopy}</p>
      <p style="margin-top:var(--space-sm); color:var(--success); font-weight:700;">${salary}</p>
      <div style="margin-top:var(--space-sm); display:flex; flex-wrap:wrap; gap:6px;">${tags}</div>
      ${url ? `<p style="margin-top:var(--space-sm);"><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Open source</a></p>` : ''}
    </article>`;
}

function renderUnresolvedCandidateCard(item) {
  const title = escapeHtml(item?.title || 'Untitled live candidate');
  const company = escapeHtml(item?.company || item?.restaurant_name || 'Company unavailable');
  const restaurant = escapeHtml(item?.restaurant_name || '');
  const address = escapeHtml(item?.resolved_address || 'No exact address resolved');
  const provider = escapeHtml(item?.provider || item?.source || 'provider unavailable');
  const url = safeJobHref(item?.source_url || item?.url || '');
  const reasons = Array.isArray(item?.reasons) ? item.reasons : [];
  const tags = Array.isArray(item?.tags) ? item.tags : [];

  return `
    <article class="job-card card" style="margin-bottom:var(--space-md);border-color:var(--warning);">
      <div style="display:flex;justify-content:space-between;gap:var(--space-md);align-items:flex-start;">
        <div>
          <h3>${title}</h3>
          <p class="muted">${company}${restaurant && restaurant !== company ? ` · ${restaurant}` : ''}</p>
          <p class="muted">${address}</p>
          <p class="muted">${escapeHtml(item?.radius_label || 'Radius not verified')} · ${escapeHtml(item?.commute_label || 'Commute not verified')}</p>
        </div>
        <span class="badge badge-budget-guarded">Needs resolution</span>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:var(--space-sm);">
        <span class="badge badge-cached">provider: ${provider}</span>
        ${reasons.map(reason => `<span class="badge badge-budget-guarded">${escapeHtml(reason)}</span>`).join('')}
        ${tags.slice(0, 6).map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
      </div>
      ${url ? `<p style="margin-top:var(--space-sm);"><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Open source</a></p>` : ''}
    </article>`;
}
