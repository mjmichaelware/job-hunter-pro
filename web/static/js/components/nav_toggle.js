/* components/nav_toggle.js — collapsible / retractable left nav rail.
   Toggles data-nav on .app-shell; persists; defaults collapsed on narrow phones
   so the content gets full width, expanded on wider screens. */

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
  const cur = shell ? shell.getAttribute('data-nav') : 'open';
  setNav(cur === 'open' ? 'collapsed' : 'open');
}

function initNav() {
  let saved = null;
  try { saved = localStorage.getItem('jhp_nav'); } catch (e) {}
  // default: collapsed on phones (<720px), open on larger screens
  const def = (window.matchMedia && window.matchMedia('(max-width: 719px)').matches) ? 'collapsed' : 'open';
  setNav(saved || def);
  const btn = document.getElementById('nav-toggle');
  if (btn) btn.addEventListener('click', toggleNav);
  // on a phone, picking a nav item should auto-collapse the rail back
  const nav = document.getElementById('main-nav');
  if (nav) nav.addEventListener('click', function (e) {
    if (e.target.closest('.nav-btn') && window.matchMedia('(max-width: 719px)').matches) setNav('collapsed');
  });
}
