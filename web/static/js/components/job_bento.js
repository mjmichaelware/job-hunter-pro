/* components/job_bento.js — a job as a glass Bento tile. Density adapts to the
   layout toggle (full list → micro grid). Every field null-guarded; provider
   dicts (e.g. Adzuna location) are coerced to text, never stringified raw. */

// Coerce any value that might be a provider dict into clean display text.
function cleanText(v, fallback) {
  if (v == null || v === '') return fallback;
  if (typeof v === 'string') return v;
  if (typeof v === 'object') {
    if (v.display_name) return String(v.display_name);
    if (Array.isArray(v.area) && v.area.length) return v.area.slice(-2).join(', ');
    if (Array.isArray(v)) return v.join(', ');
    return fallback;
  }
  return String(v);
}

function _matchBadge(job) {
  const v = pick(job, ['match', 'match_score'], null);
  if (v == null) return '';
  const cls = Number(v) >= 80 ? 'badge-safe' : Number(v) >= 50 ? 'badge-warn' : 'badge-error';
  const flash = Number(v) >= 80 ? ' flash' : '';
  return '<span class="badge ' + cls + flash + '">match ' + esc(String(v)) + '</span>';
}

function _researchLinks(company) {
  if (!company || company === 'Company not listed') return '';
  const q = encodeURIComponent(company);
  return '<details class="research-links"><summary class="research-links__toggle">▸ Research</summary>'
    + '<div class="research-links__row">'
    + '<a class="btn-link" href="https://www.glassdoor.com/Search/results.htm?keyword=' + q + '" target="_blank" rel="noopener noreferrer">Glassdoor</a>'
    + '<a class="btn-link" href="https://www.bbb.org/search?find_text=' + q + '" target="_blank" rel="noopener noreferrer">BBB</a>'
    + '<a class="btn-link" href="https://www.google.com/search?q=' + q + '+reviews+jobs" target="_blank" rel="noopener noreferrer">Google</a>'
    + '<a class="btn-link" href="https://news.google.com/search?q=' + q + '" target="_blank" rel="noopener noreferrer">News</a>'
    + '</div></details>';
}

function bentoJobCard(job, isUnresolved) {
  const density = (typeof layoutDensity === 'function') ? layoutDensity() : 'full';
  const title = esc(cleanText(pick(job, ['title', 'job_title', 'name'], null), 'Untitled role'));
  const company = esc(cleanText(pick(job, ['company', 'company_name', 'restaurant_name', 'employer', 'place_name'], null), 'Company not listed'));
  const location = esc(cleanText(pick(job, ['resolved_address', 'normalized_address', 'location', 'listing_location'], null), 'Location not resolved'));
  const source = esc(cleanText(pick(job, ['source', '_provider', 'provider', 'via'], null), ''));
  const url = href(pick(job, ['source_url', 'url', 'apply_url', 'share_link'], ''));
  const salaryRaw = pick(job, ['salary'], null);
  const salary = (salaryRaw && !/not listed/i.test(salaryRaw)) ? esc(cleanText(salaryRaw, '')) : '';
  const postedRaw = pick(job, ['published_date', 'posted_date', 'created', 'date'], null);
  const posted = postedRaw ? esc(cleanText(postedRaw, '')) : '';
  const gauge = (typeof reviewGauge === 'function') ? reviewGauge(pick(job, ['review_score'], null), pick(job, ['google_rating'], null)) : '';
  const matchBadge = _matchBadge(job);
  const flags = Array.isArray(job.resolution_flags) ? job.resolution_flags : [];
  const cls = 'bento bento--' + density + (isUnresolved ? ' bento--unresolved' : '');
  const uid = 'job-' + Math.random().toString(36).slice(2, 9);

  let body = '<div class="bento__head"><div><div class="bento__title">' + title + '</div>'
    + '<div class="bento__company">' + company + (source ? ' · <span class="source-chip">' + source + '</span>' : '') + '</div></div>'
    + '<div class="bento__badges">' + matchBadge + '</div></div>';

  if (density === 'full' || density === 'key') {
    body += '<div class="bento__meta">'
      + '<span class="bento__loc">' + location + '</span>'
      + (salary ? '<span class="badge badge-cached">' + salary + '</span>' : '')
      + (posted ? '<span class="tag">' + posted + '</span>' : '')
      + '</div>';
  }

  if (density === 'full') {
    const companyRaw = cleanText(pick(job, ['company', 'company_name', 'restaurant_name', 'employer', 'place_name'], null), '');
    body += '<div class="bento__tiles">'
      + '<div class="tile"><div class="tile__label">Core</div>' + gauge + '</div>'
      + '<div class="tile"><div class="tile__label">Commute</div><div class="tile__value' + (job.commute_seconds == null ? ' na' : '') + '">' + esc(formatMins(job.commute_seconds)) + '</div></div>'
      + '<div class="tile"><div class="tile__label">Radius</div><div class="tile__value' + (job.radius_miles == null ? ' na' : '') + '">' + esc(formatMiles(job.radius_miles)) + '</div></div>'
      + '</div>'
      + (flags.length ? '<div class="bento__flags">' + tagList(flags) + '</div>' : '')
      + (url ? '<div class="bento__actions"><a href="' + esc(url) + '" target="_blank" rel="noopener" class="btn-link" data-stop>' + esc(t('common.apply')) + '</a></div>' : '')
      + _researchLinks(companyRaw);
  } else if (density === 'key') {
    body += '<div class="bento__minirow">' + gauge + '</div>';
  } else if (density === 'tight') {
    body += '<div class="bento__minirow">' + (gauge || '') + '</div>';
  }
  // micro: head + match badge only (already in body)

  return '<article class="' + cls + '" data-job="' + uid + '" tabindex="0" role="button" aria-label="' + title + ' — view evidence">' + body + '</article>';
}

function wireBentoCards(container, jobs) {
  container.querySelectorAll('.bento[data-job]').forEach(function (card, i) {
    function open(e) { if (e.target.closest('[data-stop]')) return; openEvidence(jobs[i]); }
    card.addEventListener('click', open);
    card.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(e); } });
  });
}
