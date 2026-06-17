/* views/render_opportunities.js — Places radar. Honest about the disabled state:
   if the backend has it off for cost control, show the enable notice — NOT a fake list. */

async function loadOpportunitiesView() {
  const data = await safeFetch('/api/opportunities');
  const el = mount(); if (!el) return;
  if (!data) { renderState(el, 'state-error', 'Could not load opportunities.'); return; }
  JHP_SYNC.remember('opportunities', data);

  if (data.enabled === false || data.status === 'disabled') {
    el.innerHTML = '<div class="info-box info-box--warn"><strong>Opportunities disabled:</strong> '
      + esc(data.reason || data.message || 'This feature is not enabled in the current configuration.') + '</div>';
    return;
  }

  const opps = arr(data, ['data', 'opportunities']);
  let html = '';
  if (data.count != null) html += '<p class="status-line">' + esc(String(data.count)) + ' opportunities returned.</p>';
  if (!opps.length) {
    html += '<p class="state-empty">No opportunities returned. The feature may need a location origin or configuration.</p>';
    el.innerHTML = html; return;
  }

  html += '<div class="opp-list">' + opps.map(function (o) {
    const rating = pick(o, ['google_rating', 'rating'], null);
    const radius = pick(o, ['radius_miles'], null);
    const maps = href(pick(o, ['google_maps_url', 'url'], ''));
    return '<div class="opp-card"><div class="opp-card__name">' + esc(pick(o, ['name', 'place_name'], 'Unnamed')) + '</div>'
      + '<div class="opp-card__addr">' + esc(pick(o, ['resolved_address', 'address', 'vicinity'], 'Address unavailable')) + '</div>'
      + '<div class="opp-card__meta">'
      + (rating != null ? '<span class="badge badge-safe">rating ' + esc(String(rating)) + '</span> ' : '<span class="na">rating unavailable</span> ')
      + (radius != null ? '<span class="tag">' + esc(formatMiles(radius)) + '</span> ' : '')
      + (maps ? '<a class="btn-link" href="' + esc(maps) + '" target="_blank" rel="noopener">Map</a>' : '')
      + '</div></div>';
  }).join('') + '</div>';
  el.innerHTML = html;
}

registerView('opportunities', 'Opportunities', loadOpportunitiesView);
