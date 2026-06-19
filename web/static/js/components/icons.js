/* components/icons.js — inline SVG icon system. Stroke-based, currentColor, so
   theme + industry accent cascade through automatically. Pure strings, no deps. */

const _ICON_PATHS = {
  home: '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
  jobs: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
  discovery: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
  opportunities: '<path d="M12 2v4M12 18v4M2 12h4M18 12h4"/><circle cx="12" cy="12" r="4"/>',
  history: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  applications: '<path d="M9 11l3 3 6-6"/><rect x="3" y="4" width="18" height="16" rx="2"/>',
  providers: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  budget: '<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
  debug: '<rect x="5" y="6" width="14" height="14" rx="3"/><path d="M9 6V4M15 6V4M5 11H2M22 11h-3M5 16H2M22 16h-3M9 11h6"/>',
  'why-three': '<path d="M12 2l3 6 6 .9-4.5 4.2 1 6L12 16l-5.5 3 1-6L3 8.9 9 8z"/>',
  diagnostics: '<path d="M3 12h4l2 5 4-12 2 7h6"/>',
  system: '<path d="M3 12h4l2 5 4-12 2 7h6"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
  filter: '<path d="M3 5h18l-7 8v6l-4 2v-8z"/>',
  sort: '<path d="M7 4v16M7 4l-3 3M7 4l3 3M17 20V4M17 20l-3-3M17 20l3-3"/>',
  layout: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 9v12"/>',
  apply: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  track: '<circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/>',
  external: '<path d="M14 4h6v6M20 4l-8 8M18 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6"/>',
  check: '<path d="M5 12l4 4L19 6"/>',
  alert: '<path d="M12 2l10 18H2z"/><path d="M12 9v5M12 17h.01"/>',
  key: '<circle cx="8" cy="14" r="4"/><path d="M11 11l9-9M17 5l3 3M14 8l3 3"/>',
  lock: '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  spark: '<path d="M12 3v6M12 15v6M3 12h6M15 12h6M6 6l3 3M15 15l3 3M18 6l-3 3M9 15l-3 3"/>',
  rocket: '<path d="M5 15l-2 6 6-2M9 11a8 8 0 0 1 8-8c2 0 3 1 3 3a8 8 0 0 1-8 8l-3 3-3-3z"/><circle cx="14" cy="10" r="1.5"/>',
  pin: '<path d="M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/>',
};

function icon(name, opts) {
  const p = _ICON_PATHS[name];
  if (!p) return '';
  const o = opts || {};
  const size = o.size || 20;
  const cls = 'icon' + (o.cls ? ' ' + o.cls : '');
  return '<svg class="' + cls + '" width="' + size + '" height="' + size + '" viewBox="0 0 24 24" '
    + 'fill="none" stroke="currentColor" stroke-width="' + (o.weight || 1.8) + '" '
    + 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + p + '</svg>';
}
