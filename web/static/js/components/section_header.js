/* components/section_header.js — branded glassy header reused by every view, so
   branding + "what this does" copy stays consistent. Plus an illustrated empty
   state. Real copy only — never fake metrics. */

function sectionHeader(o) {
  o = o || {};
  const ic = o.icon ? icon(o.icon, { size: 26 }) : '';
  return '<header class="section-header">'
    + '<div class="section-header__bar">'
    + (ic ? '<span class="section-header__icon">' + ic + '</span>' : '')
    + '<div class="section-header__text">'
    + (o.kicker ? '<div class="section-header__kicker">' + esc(o.kicker) + '</div>' : '')
    + '<h2 class="section-header__title">' + esc(o.title || '') + '</h2>'
    + '</div></div>'
    + (o.blurb ? '<p class="section-header__blurb">' + esc(o.blurb) + '</p>' : '')
    + '</header>';
}

// Illustrated empty/needs-action state. `action` = {label, go} routes to a view.
function emptyArt(o) {
  o = o || {};
  const ic = icon(o.icon || 'spark', { size: 48 });
  let html = '<div class="empty-art">'
    + '<div class="empty-art__icon">' + ic + '</div>'
    + '<div class="empty-art__title">' + esc(o.title || 'Nothing here yet') + '</div>'
    + (o.body ? '<p class="empty-art__body">' + esc(o.body) + '</p>' : '');
  if (o.action && o.action.go) {
    html += '<button type="button" class="btn btn-glow empty-art__cta" data-go="' + esc(o.action.go) + '">'
      + esc(o.action.label || 'Get started') + '</button>';
  }
  html += '</div>';
  return html;
}

// Wire any [data-go] inside a container to route (used by emptyArt CTAs).
function wireGo(el) {
  if (!el) return;
  el.querySelectorAll('[data-go]').forEach(function (n) {
    n.addEventListener('click', function () { navigate(n.dataset.go); });
  });
}
