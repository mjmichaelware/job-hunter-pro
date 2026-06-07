function normalizeJobsPayload(payload) {
  if (!payload || typeof payload !== 'object') return [];
  if (Array.isArray(payload.jobs)) return payload.jobs;
  if (Array.isArray(payload.data)) return payload.data;
  if (payload.data && Array.isArray(payload.data.jobs)) return payload.data.jobs;
  if (Array.isArray(payload.results)) return payload.results;
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

  const jobs = normalizeJobsPayload(data);

  if (!jobs.length) {
    if (data?.dry_run) {
      container.innerHTML = `
        <div class="chart-fallback">
          <strong>Live jobs are not loaded yet.</strong><br>
          ${escapeHtml(data.message || 'Dry run completed without spending discovery provider budget.')}<br>
          Use <strong>Run Live Discovery</strong> when ready to spend provider budget.
        </div>`;
      return;
    }

    container.innerHTML = live
      ? '<div class="chart-fallback">Live discovery returned no accepted jobs for the current filters.</div>'
      : '<div class="chart-fallback">No live jobs loaded. Run live discovery when ready to spend provider budget.</div>';
    return;
  }

  let filtered = jobs.filter((job) => {
    const industry = pickJobField(job, ['industry', 'industry_key'], '');
    const radius = jobNumber(pickJobField(job, ['haversine_radius_miles', 'radius_miles', 'distance_miles'], null), null);
    const match = jobNumber(pickJobField(job, ['match_score', 'score', 'resonance_score'], null), null);

    if (AppState.filters?.industry && industry && industry !== AppState.filters.industry) return false;
    if (radius !== null && AppState.filters?.radius && radius > Number(AppState.filters.radius)) return false;
    if (match !== null && AppState.filters?.matchScore && match < Number(AppState.filters.matchScore)) return false;
    return true;
  });

  if (!filtered.length) {
    container.innerHTML = '<div class="chart-fallback">No live jobs match current filters. Adjust filters or run a broader discovery.</div>';
    return;
  }

  container.innerHTML = filtered.map((job) => {
    const title = escapeHtml(pickJobField(job, ['title', 'job_title', 'name'], 'Untitled role'));
    const company = escapeHtml(pickJobField(job, ['company', 'company_name', 'employer', 'place_name'], 'Company unavailable'));
    const address = escapeHtml(pickJobField(job, ['normalized_address', 'address', 'location', 'detected_location'], 'Address unresolved'));
    const source = escapeHtml(pickJobField(job, ['source', 'provider', 'source_provider_id'], 'source unavailable'));
    const salary = escapeHtml(pickJobField(job, ['salary', 'salary_hint', 'pay', 'compensation'], 'Salary not listed'));

    const match = jobNumber(pickJobField(job, ['match_score', 'score', 'resonance_score'], null), null);
    const review = jobNumber(pickJobField(job, ['review_score', 'review_heuristic_score'], null), null);
    const rating = jobNumber(pickJobField(job, ['rating', 'place_rating'], null), null);
    const reviews = jobNumber(pickJobField(job, ['review_count', 'place_review_count'], null), null);
    const transitSeconds = jobNumber(pickJobField(job, ['commute_matrix_seconds', 'transit_seconds', 'commute_seconds'], null), null);
    const radius = jobNumber(pickJobField(job, ['haversine_radius_miles', 'radius_miles', 'distance_miles'], null), null);
    const tags = [
      pickJobField(job, ['role_family'], ''),
      pickJobField(job, ['industry'], ''),
      source ? `source: ${source}` : ''
    ].filter(Boolean).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('');

    const commuteCopy = transitSeconds !== null
      ? `${Math.round(transitSeconds / 60)} min transit`
      : 'Transit unavailable';

    const distanceCopy = radius !== null
      ? `${radius.toFixed(1)} mi`
      : 'Distance unavailable';

    const scoreCopy = match !== null
      ? `${Math.round(match)}% match`
      : 'Match unavailable';

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
      </article>`;
  }).join('');
}
