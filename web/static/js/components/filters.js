/* components/filters.js — local-first filter panel + chips.
   Filters operate on already-loaded saved jobs (no quota). A filter whose backing
   field is null across ALL current results is disabled with honest copy. */

const FILTER_FIELDS = [
  { id: 'min_match', label: 'Min match score', type: 'number', min: 0, max: 100, field: ['match', 'match_score'] },
  { id: 'min_rating', label: 'Min Google rating', type: 'number', min: 0, max: 5, step: 0.1, field: ['google_rating'] },
  { id: 'max_radius', label: 'Max radius (mi)', type: 'number', min: 0, max: 50, step: 0.5, field: ['radius_miles'] },
  { id: 'max_transit', label: 'Max transit (min)', type: 'number', min: 0, max: 120, field: ['commute_seconds'] },
  { id: 'q', label: 'Role / keyword', type: 'text', field: null },
];

function fieldPresent(jobs, keys) {
  if (!keys) return true;
  return jobs.some(function (j) { return pick(j, keys, null) != null; });
}

function renderFilters(filters, industries, jobs) {
  const fv = filters || {};
  const indOpts = (industries || []).map(function (i) {
    return '<option value="' + esc(i.key) + '"' + (fv.industry === i.key ? ' selected' : '') + '>' + esc(i.label) + '</option>';
  }).join('');
  let grid = '<label>Industry<select id="f-industry"><option value="">All</option>' + indOpts + '</select></label>';
  FILTER_FIELDS.forEach(function (f) {
    const present = fieldPresent(jobs || [], f.field);
    const dis = present ? '' : ' disabled';
    const note = present ? '' : ' <span class="na">(unavailable — FAST_JOBS)</span>';
    const step = f.step ? ' step="' + f.step + '"' : '';
    const rng = f.type === 'number' ? ' min="' + f.min + '" max="' + f.max + '"' + step : '';
    grid += '<label>' + esc(f.label) + note + '<input type="' + f.type + '" id="f-' + f.id + '"' + rng
      + ' value="' + esc(fv[f.id] || '') + '"' + dis + '></label>';
  });
  return '<details class="filter-panel"><summary>Filters (local only — no quota spent)</summary>'
    + '<div class="filter-grid">' + grid + '</div>'
    + '<div class="filter-actions">'
    + '<button type="button" id="btn-apply-filters" class="btn">Apply</button>'
    + '<button type="button" id="btn-clear-filters" class="btn">Clear</button>'
    + '</div></details>';
}

function readFilters(container) {
  const f = {};
  const ind = container.querySelector('#f-industry');
  if (ind && ind.value) f.industry = ind.value;
  FILTER_FIELDS.forEach(function (fld) {
    const el = container.querySelector('#f-' + fld.id);
    if (el && !el.disabled && el.value !== '') f[fld.id] = el.value;
  });
  return f;
}

// Filter loaded jobs client-side (honest: only on fields the jobs actually carry).
function applyLocalFilters(jobs, f) {
  if (!f) return jobs;
  return jobs.filter(function (j) {
    if (f.min_match != null && pick(j, ['match', 'match_score'], null) != null && Number(pick(j, ['match', 'match_score'], 0)) < Number(f.min_match)) return false;
    if (f.min_rating != null && j.google_rating != null && Number(j.google_rating) < Number(f.min_rating)) return false;
    if (f.max_radius != null && j.radius_miles != null && Number(j.radius_miles) > Number(f.max_radius)) return false;
    if (f.max_transit != null && j.commute_seconds != null && Number(j.commute_seconds) / 60 > Number(f.max_transit)) return false;
    if (f.industry && pick(j, ['industry', 'role_family'], '') !== f.industry) return false;
    if (f.q) {
      const hay = JSON.stringify(j).toLowerCase();
      if (hay.indexOf(String(f.q).toLowerCase()) === -1) return false;
    }
    return true;
  });
}

function renderChips(filters) {
  const f = filters || {};
  const keys = Object.keys(f).filter(function (k) { return f[k] !== '' && f[k] != null; });
  if (!keys.length) return '';
  return '<div class="chip-strip">' + keys.map(function (k) {
    return '<span class="chip">' + esc(k) + ': ' + esc(String(f[k]))
      + '<button type="button" class="chip__x" data-chip="' + esc(k) + '" aria-label="Remove ' + esc(k) + '">×</button></span>';
  }).join('') + '</div>';
}
