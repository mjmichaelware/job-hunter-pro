/* components/competitor_audit.js — per-employer market comparison built ONLY from
   the real loaded batch. For a job's employer it shows: how many postings that
   employer has in view, its Google rating, and how that rating ranks against the
   other employers in the same role family. No fabricated competitors; thin data
   yields an honest "not enough data" note. Exposes competitorAuditHtml(job). */

var _cohort = [];

function setCohort(jobs) { _cohort = Array.isArray(jobs) ? jobs : []; }

function _coName(j) { return String(pick(j, ['company', 'company_name', 'restaurant_name'], '') || '').trim(); }
function _fam(j) { return String(pick(j, ['role_family', 'industry'], '') || '').toLowerCase(); }
function _rating(j) { const r = pick(j, ['google_rating'], null); const n = Number(r); return isNaN(n) ? null : n; }

function competitorAuditHtml(job) {
  const name = _coName(job);
  if (!name || !_cohort.length) return '';
  const fam = _fam(job);
  const peers = _cohort.filter(function (j) { return !fam || _fam(j) === fam; });
  if (peers.length < 3) {
    return '<div class="audit-sec"><h4 class="research-sec__title">Market audit</h4>'
      + '<p class="na">Not enough postings in this role family yet to compare employers.</p></div>';
  }
  // group peers by employer
  const byCo = {};
  peers.forEach(function (j) {
    const c = _coName(j); if (!c) return;
    if (!byCo[c]) byCo[c] = { count: 0, ratings: [] };
    byCo[c].count += 1;
    const r = _rating(j); if (r != null) byCo[c].ratings.push(r);
  });
  const mine = byCo[name] || { count: 1, ratings: [] };
  const myRating = mine.ratings.length ? (mine.ratings.reduce(function (a, b) { return a + b; }, 0) / mine.ratings.length) : null;
  // rank employers that have a rating
  const rated = Object.keys(byCo).map(function (c) {
    const rs = byCo[c].ratings;
    return { co: c, avg: rs.length ? rs.reduce(function (a, b) { return a + b; }, 0) / rs.length : null };
  }).filter(function (x) { return x.avg != null; }).sort(function (a, b) { return b.avg - a.avg; });
  let rankLine = '<p class="na">No Google rating resolved for this employer yet.</p>';
  if (myRating != null && rated.length) {
    const idx = rated.findIndex(function (x) { return x.co === name; });
    const pos = idx >= 0 ? (idx + 1) : null;
    rankLine = '<p>Rated <b>' + myRating.toFixed(1) + '</b>'
      + (pos ? ' — ranks <b>#' + pos + '</b> of ' + rated.length + ' rated employers in this role family.' : '.') + '</p>';
  }
  return '<div class="audit-sec"><h4 class="research-sec__title">Market audit · ' + esc(name) + '</h4>'
    + '<div class="audit-stats">'
    + '<span class="badge badge-cached">' + mine.count + ' posting' + (mine.count === 1 ? '' : 's') + ' in view</span>'
    + '<span class="badge badge-cached">' + peers.length + ' peers in role family</span>'
    + '</div>' + rankLine + '</div>';
}
