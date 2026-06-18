/* components/layout_toggle.js — List / 2× / 3× / 4× grid density.
   Persists to localStorage. Density tier drives how much each job card shows
   (read by job_bento.js via AppState.layout). */

const LAYOUTS = [
  { id: 'cols-1', label: 'List' },
  { id: 'cols-2', label: '2×' },
  { id: 'cols-3', label: '3×' },
  { id: 'cols-4', label: '4×' },
];

(function initLayout() {
  try { const v = localStorage.getItem('jhp_layout'); if (v) AppState.layout = v; } catch (e) {}
})();

function setLayout(id) {
  AppState.layout = id;
  try { localStorage.setItem('jhp_layout', id); } catch (e) {}
}

// density tier: 'full' (list), 'key' (2×), 'tight' (3×), 'micro' (4×)
function layoutDensity() {
  return { 'cols-1': 'full', 'cols-2': 'key', 'cols-3': 'tight', 'cols-4': 'micro' }[AppState.layout] || 'full';
}

function renderLayoutToggle() {
  const cur = AppState.layout || 'cols-1';
  return '<div class="seg" role="group" aria-label="Layout">' + LAYOUTS.map(function (l) {
    return '<button type="button" class="seg__btn' + (l.id === cur ? ' is-active' : '') + '" data-layout="' + l.id + '">' + esc(l.label) + '</button>';
  }).join('') + '</div>';
}
