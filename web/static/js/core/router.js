/* core/router.js — hash router, nav builder, boot sequence.
   Boot is SAFE: it only calls /api/health (render_health) and lets the default
   Jobs view load saved batches. It NEVER triggers live discovery or /api/ingest. */

function buildNav() {
  const nav = document.getElementById('main-nav');
  if (!nav) return;
  nav.innerHTML = '';
  for (const id of Object.keys(Views)) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'nav-btn';
    btn.dataset.view = id;
    btn.textContent = (typeof t === 'function' ? t('nav.' + id) : null) || Views[id].label;
    btn.addEventListener('click', function () { navigate(id); });
    nav.appendChild(btn);
  }
  updateNavActive(AppState.activeView);
}

function updateNavActive(viewId) {
  document.querySelectorAll('.nav-btn').forEach(function (btn) {
    btn.classList.toggle('nav-active', btn.dataset.view === viewId);
  });
}

function setViewTitle(title) {
  const el = document.getElementById('view-title');
  if (el) el.textContent = title;
}

async function navigate(viewId) {
  const view = Views[viewId];
  if (!view) return;
  AppState.activeView = viewId;
  updateNavActive(viewId);
  setViewTitle((typeof t === 'function' ? t('nav.' + viewId) : null) || view.label);
  if (window.location.hash !== '#' + viewId) window.location.hash = '#' + viewId;

  const node = mount();
  function run() {
    if (node) { node.innerHTML = '<p class="state-loading">' + esc(t('state.init')) + '</p>'; node.classList.add('view-enter'); }
    Promise.resolve()
      .then(function () { return view.load(); })
      .catch(function (err) { if (node) node.innerHTML = '<p class="state-error">Error loading view: ' + esc(err.message) + '</p>'; });
  }
  // Morphic view transition where supported, else instant swap.
  if (document.startViewTransition && !A11y.prefersReducedMotion()) document.startViewTransition(run);
  else run();
}

function routeFromHash() {
  const hash = window.location.hash.replace('#', '').trim();
  return (hash && Views[hash]) ? hash : 'jobs';
}

window.addEventListener('hashchange', function () { navigate(routeFromHash()); });

document.addEventListener('DOMContentLoaded', function () {
  // language selector
  const langSel = document.getElementById('lang-select');
  if (langSel) langSel.addEventListener('change', function (e) { setLang(e.target.value); });

  // command palette trigger + ⌘K / Ctrl+K
  const cmdBtn = document.getElementById('btn-command');
  if (cmdBtn && typeof openCommandPalette === 'function') cmdBtn.addEventListener('click', openCommandPalette);
  window.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k' && typeof openCommandPalette === 'function') {
      e.preventDefault(); openCommandPalette();
    }
  });

  applyI18n(document);
  buildNav();
  if (typeof renderHealth === 'function') renderHealth();   // safe: /api/health only
  if (typeof initVolumetric === 'function') initVolumetric();
  navigate(routeFromHash());
});
