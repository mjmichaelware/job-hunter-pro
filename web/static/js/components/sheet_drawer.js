/* components/sheet_drawer.js — generic spring bottom-sheet host.
   Any feature (evidence, filters) calls openSheet(title, html, onMount).
   Handles focus trap, scrim/Esc close, and the elastic spring animation. */

let _sheetRelease = null;

function openSheet(title, bodyHtml, onMount) {
  const host = document.getElementById('sheet-host');
  const titleEl = document.getElementById('sheet-title');
  const bodyEl = document.getElementById('sheet-body');
  if (!host || !bodyEl) return;

  titleEl.textContent = title || '';
  bodyEl.innerHTML = bodyHtml || '';
  host.hidden = false;
  host.setAttribute('aria-hidden', 'false');
  host.classList.remove('is-closing');

  if (typeof onMount === 'function') onMount(bodyEl);
  _sheetRelease = A11y.trapFocus(host.querySelector('.sheet'));

  host.querySelectorAll('[data-sheet-close]').forEach(function (el) {
    el.addEventListener('click', closeSheet, { once: true });
  });
  document.addEventListener('keydown', _sheetEsc);
  if (typeof announce === 'function') announce(title ? title + ' opened' : 'Panel opened');
}

function _sheetEsc(e) { if (e.key === 'Escape') closeSheet(); }

function closeSheet() {
  const host = document.getElementById('sheet-host');
  if (!host || host.hidden) return;
  document.removeEventListener('keydown', _sheetEsc);

  function finish() {
    host.hidden = true;
    host.setAttribute('aria-hidden', 'true');
    host.classList.remove('is-closing');
    const body = document.getElementById('sheet-body');
    if (body) body.innerHTML = '';
    if (_sheetRelease) { _sheetRelease(); _sheetRelease = null; }
  }

  if (A11y.prefersReducedMotion()) { finish(); return; }
  host.classList.add('is-closing');
  window.setTimeout(finish, 300);
}
