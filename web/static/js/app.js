/* app.js — hash router, AppState, nav, view dispatcher.
   No hardcoded jobs, counts, or any fake data. */

const AppState = {
  activeView: 'jobs',
  filters: {},
  cache: {},
};

// All registered views: id -> { label, load }
const Views = {};

function registerView(id, label, loadFn) {
  Views[id] = { id, label, load: loadFn };
}

// Build nav bar from registered views
function buildNav() {
  const nav = document.getElementById('main-nav');
  if (!nav) return;
  nav.innerHTML = '';
  for (const [id, view] of Object.entries(Views)) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'nav-btn';
    btn.dataset.view = id;
    btn.textContent = view.label;
    btn.addEventListener('click', () => navigate(id));
    nav.appendChild(btn);
  }
}

function updateNavActive(viewId) {
  document.querySelectorAll('.nav-btn').forEach(btn => {
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
  setViewTitle(view.label);
  window.location.hash = '#' + viewId;
  const mount = document.getElementById('view-mount');
  if (mount) {
    mount.innerHTML = '<p class="state-loading">Loading…</p>';
  }
  try {
    await view.load();
  } catch (err) {
    if (mount) mount.innerHTML = '<p class="state-error">Error loading view: ' + esc(err.message) + '</p>';
  }
}

// Tiny hash router
function routeFromHash() {
  const hash = window.location.hash.replace('#', '').trim();
  return (hash && Views[hash]) ? hash : 'jobs';
}

window.addEventListener('hashchange', () => navigate(routeFromHash()));

// Boot: load health strip, build nav, route to initial view
document.addEventListener('DOMContentLoaded', async () => {
  buildNav();
  // Load health strip (safe, no quota)
  const health = await safeFetch('/api/health');
  const strip = document.getElementById('health-strip');
  if (strip) {
    if (health) {
      const ver = esc(health.version || 'unknown');
      const st = health.status === 'ok' ? 'badge-safe' : 'badge-error';
      strip.innerHTML = '<span class="badge ' + st + '">' + esc(health.status || 'unknown') + '</span> v:' + ver;
    } else {
      strip.innerHTML = '<span class="badge badge-error">backend unreachable</span>';
    }
  }
  navigate(routeFromHash());
});
