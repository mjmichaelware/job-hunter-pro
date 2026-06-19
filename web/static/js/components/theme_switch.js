/* components/theme_switch.js — selectable color themes (not just light/dark).
   Sets <html data-theme>, persists to localStorage, restores on boot. */

const THEMES = [
  { id: 'cyan', label: 'Cyan' },
  { id: 'blue', label: 'Blue' },
  { id: 'green', label: 'Green' },
  { id: 'red', label: 'Red' },
  { id: 'violet', label: 'Violet' },
  { id: 'amber', label: 'Amber' },
  { id: 'mono', label: 'Mono' },
  { id: 'light', label: 'Light' },
];

function applyTheme(id) {
  const t = THEMES.some(function (x) { return x.id === id; }) ? id : 'cyan';
  document.documentElement.setAttribute('data-theme', t);
  try { localStorage.setItem('jhp_theme', t); } catch (e) {}
}

function initTheme() {
  let saved = 'cyan';
  try { saved = localStorage.getItem('jhp_theme') || 'cyan'; } catch (e) {}
  applyTheme(saved);
  const sel = document.getElementById('theme-select');
  if (sel) {
    sel.innerHTML = THEMES.map(function (x) {
      return '<option value="' + x.id + '"' + (x.id === saved ? ' selected' : '') + '>' + x.label + '</option>';
    }).join('');
    sel.addEventListener('change', function (e) { applyTheme(e.target.value); });
  }
}
