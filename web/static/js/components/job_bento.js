/* components/job_bento.js — a single job rendered as a glass Bento tile.
   Nested tiles surface trust gauge, commute, radius. Tap morphs to evidence.
   Every field null-guarded: missing data shows "unavailable", never a fake value. */

function bentoJobCard(job, isUnresolved) {
  const title = esc(pick(job, ['title', 'job_title', 'name'], 'Untitled role'));
  const company = esc(pick(job, ['company', 'company_name', 'restaurant_name', 'employer', 'place_name'], 'Company not listed'));
  const location = esc(pick(job, ['resolved_address', 'normalized_address', 'location', 'listing_location'], 'Location not resolved'));
  const source = esc(pick(job, ['source', '_provider', 'provider', 'via'], ''));
  const url = href(pick(job, ['source_url', 'url', 'apply_url', 'share_link'], ''));

  const matchVal = pick(job, ['match', 'match_score'], null);
  const matchCls = matchVal == null ? '' : (Number(matchVal) >= 80 ? 'badge-safe' : Number(matchVal) >= 50 ? 'badge-warn' : 'badge-error');
  const matchBadge = matchVal != null ? '<span class="badge ' + matchCls + '">match ' + esc(String(matchVal)) + '</span>' : '';
  const riskVal = pick(job, ['risk_level'], null);
  const riskBadge = riskVal != null ? '<span class="badge badge-disabled">risk ' + esc(String(riskVal)) + '</span>' : '';

  const flags = [].concat(Array.isArray(job.resolution_flags) ? job.resolution_flags : []);
  const cls = 'bento' + (isUnresolved ? ' bento--unresolved' : '');
  const uid = 'job-' + Math.random().toString(36).slice(2, 9);

  return '<article class="' + cls + '" data-job="' + uid + '" tabindex="0" role="button" aria-label="' + title + ' — view evidence">'
    + '<div class="bento__head">'
    + '<div><div class="bento__title">' + title + '</div>'
    + '<div class="bento__company">' + company + (source ? ' · <span class="source-chip">' + source + '</span>' : '') + '</div></div>'
    + '<div class="bento__badges">' + matchBadge + riskBadge + '</div>'
    + '</div>'
    + '<div class="bento__company">' + location + '</div>'
    + '<div class="bento__tiles">'
    + '<div class="tile"><div class="tile__label">Trust</div>' + reviewGauge(pick(job, ['review_score'], null), pick(job, ['google_rating'], null)) + '</div>'
    + '<div class="tile"><div class="tile__label">Commute</div><div class="tile__value' + (job.commute_seconds == null ? ' na' : '') + '">' + esc(formatMins(job.commute_seconds)) + '</div></div>'
    + '<div class="tile"><div class="tile__label">Radius</div><div class="tile__value' + (job.radius_miles == null ? ' na' : '') + '">' + esc(formatMiles(job.radius_miles)) + '</div></div>'
    + '</div>'
    + (flags.length ? '<div class="bento__flags">' + tagList(flags) + '</div>' : '')
    + (url ? '<div class="bento__actions"><a href="' + esc(url) + '" target="_blank" rel="noopener" class="btn-link" data-stop>' + esc(t('common.apply')) + '</a></div>' : '')
    + '</article>';
}

// Wire tap/Enter on every Bento card in a container to open its evidence sheet.
function wireBentoCards(container, jobs) {
  const cards = container.querySelectorAll('.bento[data-job]');
  cards.forEach(function (card, i) {
    function open(e) {
      if (e.target.closest('[data-stop]')) return; // let Apply link work
      openEvidence(jobs[i]);
    }
    card.addEventListener('click', open);
    card.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(e); } });
  });
}
