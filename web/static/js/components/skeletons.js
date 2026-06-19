/* components/skeletons.js — shimmer placeholders for loading states.
   Uses the existing .skeleton shimmer (animations.css). Truth-safe: a skeleton
   is an honest "loading" affordance, never fabricated data. */

function _skLines(widths) {
  return widths.map(function (w) {
    return '<div class="skeleton skeleton-line" style="width:' + w + '"></div>';
  }).join('');
}

/* skeletonCards(n, kind) → HTML string of n placeholder cards.
   kind: 'job' | 'stat' | 'row' | 'provider' */
function skeletonCards(n, kind) {
  n = n || 3;
  kind = kind || 'row';
  var out = [];
  for (var i = 0; i < n; i++) {
    if (kind === 'stat' || kind === 'provider') {
      out.push('<div class="skeleton-card skeleton-card--stat">' + _skLines(['60%', '40%']) + '</div>');
    } else if (kind === 'job') {
      out.push('<div class="skeleton-card">' + _skLines(['70%', '45%', '90%']) + '</div>');
    } else {
      out.push('<div class="skeleton-card skeleton-card--row">' + _skLines(['85%', '55%']) + '</div>');
    }
  }
  var wrap = (kind === 'stat' || kind === 'provider') ? 'card-row card-row--wrap' : 'skeleton-stack';
  return '<div class="' + wrap + '" aria-busy="true" aria-label="Loading">' + out.join('') + '</div>';
}
