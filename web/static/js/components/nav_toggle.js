/* components/nav_toggle.js — collapsible / retractable left nav rail.
   Defaults collapsed on ALL screen sizes on first visit.
   Saved localStorage 'jhp_nav' preference is honored if present.
   First-visit: attention pulse + "Menu" hint label on the toggle button. */

function setNav(state) {
  const shell = document.querySelector('.app-shell');
  if (!shell) return;
  shell.setAttribute('data-nav', state);
  try { localStorage.setItem('jhp_nav', state); } catch (e) {}
  const btn = document.getElementById('nav-toggle');
  if (btn) btn.setAttribute('aria-expanded', state === 'open' ? 'true' : 'false');
}

function toggleNav() {
  const shell = document.querySelector('.app-shell');
  const cur = shell ? shell.getAttribute('data-nav') : 'collapsed';
  setNav(cur === 'open' ? 'collapsed' : 'open');
  _dismissNavHint();
}

function _dismissNavHint() {
  const hint = document.getElementById('nav-hint-label');
  const btn = document.getElementById('nav-toggle');
  if (hint) hint.remove();
  if (btn) btn.classList.remove('nav-toggle--pulse');
}

function _showNavHint() {
  const btn = document.getElementById('nav-toggle');
  if (!btn) return;
  btn.classList.add('nav-toggle--pulse');
  // Brief "Menu" tooltip hint
  const hint = document.createElement('span');
  hint.id = 'nav-hint-label';
  hint.className = 'nav-hint-label';
  hint.setAttribute('aria-hidden', 'true');
  hint.textContent = 'Menu';
  btn.parentNode.style.position = 'relative';
  btn.parentNode.appendChild(hint);
  // Auto-dismiss after 3.5 s
  window.setTimeout(_dismissNavHint, 3500);
}

function initNav() {
  let saved = null;
  try { saved = localStorage.getItem('jhp_nav'); } catch (e) {}
  // Default collapsed on all screen sizes; honor saved pref if present
  setNav(saved || 'collapsed');
  const btn = document.getElementById('nav-toggle');
  if (btn) {
    btn.addEventListener('click', toggleNav);
    // Show hint only on genuine first visit (no saved pref)
    if (!saved) {
      window.setTimeout(_showNavHint, 600);
    }
  }
  const nav = document.getElementById('main-nav');
  if (nav) nav.addEventListener('click', function (e) {
    if (e.target.closest('.nav-btn') && window.matchMedia('(max-width: 719px)').matches) {
      setNav('collapsed');
    }
  });
}
