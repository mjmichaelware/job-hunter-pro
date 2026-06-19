/* components/trust_geometry.js — review-trust gauge.
   The geometry ENFORCES the 60/15/15/10 cap: the arc can never fill past the
   ceiling a low star rating allows. A 3.7-star place cannot render a full gauge,
   no matter the review_score. Distrust dies because the cap is visible. */

const GAUGE_R = 26;
const GAUGE_C = 2 * Math.PI * GAUGE_R; // circumference

// reviewScore: 0–100 (capped 60/15/15/10 server-side). rating: 0–5 stars (the ceiling).
function reviewGauge(reviewScore, rating) {
  if (reviewScore == null || reviewScore === '') {
    return '<div class="gauge gauge--na" title="No review intelligence">'
      + '<span class="gauge__na">' + esc(t('common.unavailable')) + '</span></div>';
  }
  const score = Math.max(0, Math.min(100, Number(reviewScore)));
  const hasRating = rating != null && rating !== '';
  const ceiling = hasRating ? (Math.max(0, Math.min(5, Number(rating))) / 5) * 100 : 100;
  // The gauge physically cannot exceed the rating ceiling.
  const shown = Math.min(score, ceiling);
  const offset = GAUGE_C * (1 - shown / 100);
  const capped = hasRating && score > ceiling;
  const hue = shown >= 75 ? 'var(--c-safe)' : shown >= 50 ? 'var(--c-warn)' : 'var(--c-err)';

  return '<div class="gauge" title="Review trust ' + Math.round(shown) + (capped ? ' (capped by rating)' : '') + '">'
    + '<svg viewBox="0 0 64 64" width="56" height="56" aria-hidden="true">'
    + '<circle cx="32" cy="32" r="' + GAUGE_R + '" fill="none" stroke="var(--c-border)" stroke-width="6"/>'
    + '<circle class="gauge__arc" cx="32" cy="32" r="' + GAUGE_R + '" fill="none" stroke="' + hue + '" stroke-width="6"'
    + ' stroke-linecap="round" stroke-dasharray="' + GAUGE_C.toFixed(1) + '"'
    + ' stroke-dashoffset="' + offset.toFixed(1) + '" transform="rotate(-90 32 32)"/>'
    + '</svg>'
    + '<span class="gauge__num">' + Math.round(shown) + '</span>'
    + (capped ? '<span class="gauge__cap" title="rating ceiling ' + esc(String(rating)) + '★">capped</span>' : '')
    + '</div>';
}
