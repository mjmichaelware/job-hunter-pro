/* components/command_palette.js — ⌘K / Ctrl+K spotlight.
   Filters the registered views locally. No network, no quota. */

let _cmdRelease = null;

function _cmdItems() {
  return Object.keys(Views).filter(function (id) { return !Views[id].hidden; }).map(function (id) {
    return { id: id, label: (typeof t === 'function' ? t('nav.' + id) : null) || Views[id].label };
  });
}

function openCommandPalette() {
  if (document.querySelector('.cmdk')) return;
  const overlay = document.createElement('div');
  overlay.className = 'cmdk';
  overlay.innerHTML = '<div class="cmdk__panel">'
    + '<input class="cmdk__input" type="text" placeholder="Jump to a view…" aria-label="Command search">'
    + '<div class="cmdk__list" role="listbox"></div></div>';
  document.body.appendChild(overlay);

  const input = overlay.querySelector('.cmdk__input');
  const list = overlay.querySelector('.cmdk__list');

  function paint(filter) {
    const q = (filter || '').toLowerCase();
    const items = _cmdItems().filter(function (it) { return it.label.toLowerCase().indexOf(q) !== -1 || it.id.indexOf(q) !== -1; });
    list.innerHTML = items.length
      ? items.map(function (it, i) { return '<button class="cmdk__item' + (i === 0 ? ' is-active' : '') + '" data-id="' + esc(it.id) + '">' + esc(it.label) + '<span class="cmdk__hint">#' + esc(it.id) + '</span></button>'; }).join('')
      : '<div class="cmdk__item"><span class="na">No matching view</span></div>';
    list.querySelectorAll('.cmdk__item[data-id]').forEach(function (b) {
      b.addEventListener('click', function () { closeCommandPalette(); navigate(b.dataset.id); });
    });
  }
  paint('');

  input.addEventListener('input', function () { paint(input.value); });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { const first = list.querySelector('.cmdk__item[data-id]'); if (first) { closeCommandPalette(); navigate(first.dataset.id); } }
    if (e.key === 'Escape') closeCommandPalette();
  });
  overlay.addEventListener('click', function (e) { if (e.target === overlay) closeCommandPalette(); });
  _cmdRelease = A11y.trapFocus(overlay);
}

function closeCommandPalette() {
  const overlay = document.querySelector('.cmdk');
  if (!overlay) return;
  if (_cmdRelease) { _cmdRelease(); _cmdRelease = null; }
  overlay.remove();
}
