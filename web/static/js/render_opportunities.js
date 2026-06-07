function normalizeOpportunitiesPayload(payload) {
  if (!payload || typeof payload !== 'object') return [];
  if (Array.isArray(payload.opportunities)) return payload.opportunities;
  if (Array.isArray(payload.data)) return payload.data;
  if (payload.data && Array.isArray(payload.data.opportunities)) return payload.data.opportunities;
  if (Array.isArray(payload.results)) return payload.results;
  return [];
}

async function loadOpportunities() {
  const container = document.getElementById('opportunities-container');
  if (!container) return;

  container.innerHTML = '<div class="chart-fallback">Loading cached Google Places opportunities...</div>';

  const data = await safeFetch(API_URLS.opportunities);
  AppState.cachedData.opportunities = data;
  renderOpportunitiesList(data);
}

function renderOpportunitiesList(data) {
  const container = document.getElementById('opportunities-container');
  if (!container) return;

  const opportunities = normalizeOpportunitiesPayload(data);

  if (!opportunities.length) {
    container.innerHTML = '<div class="chart-fallback">No opportunities loaded or matched current filters.</div>';
    return;
  }

  let filtered = opportunities.filter((opp) => {
    const industry = opp?.industry || opp?.industry_key || '';
    if (AppState.filters?.industry && industry && industry !== AppState.filters.industry) return false;
    return true;
  });

  if (!filtered.length) {
    container.innerHTML = '<div class="chart-fallback">No opportunities match current filters.</div>';
    return;
  }

  container.innerHTML = `
    <div class="notice">Loaded ${filtered.length} nearby restaurant opportunities.</div>
    ${filtered.map((opp) => {
      const name = escapeHtml(opp?.name || opp?.business_name || opp?.company || 'Unnamed opportunity');
      const address = escapeHtml(opp?.address || opp?.formatted_address || opp?.vicinity || 'Address unavailable');
      const rating = opp?.rating ?? opp?.place_rating ?? null;
      const reviewCount = opp?.review_count ?? opp?.user_ratings_total ?? null;
      const category = escapeHtml(opp?.category || opp?.primary_type || opp?.type || 'local opportunity');
      const ratingCopy = rating !== null && rating !== undefined ? `${rating}★` : 'Rating unavailable';
      const reviewCopy = reviewCount !== null && reviewCount !== undefined ? `${reviewCount} reviews` : 'review count unavailable';

      return `
        <article class="card" style="margin-bottom:var(--space-sm);">
          <div style="display:flex; justify-content:space-between; gap:var(--space-md); align-items:flex-start;">
            <div>
              <h3>${name}</h3>
              <p class="muted">${address}</p>
              <p class="muted">${category}</p>
            </div>
            <span class="badge badge-cached">${escapeHtml(ratingCopy)}</span>
          </div>
          <p style="margin-top:var(--space-sm);">${escapeHtml(reviewCopy)}</p>
        </article>`;
    }).join('')}`;
}
