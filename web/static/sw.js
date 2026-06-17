/* sw.js — offline dignity. Precaches the app shell + assets; serves saved-batch
   API reads stale-while-revalidate; falls back to offline.html for navigations.
   Never caches live discovery (/api/jobs) — that must always hit the network. */

const CACHE = 'jhp-shell-v1';
const SHELL = [
  '/', '/offline.html', '/static/manifest.json', '/static/assets/icons/icon.svg',
  '/static/css/base.css', '/static/css/a11y.css', '/static/css/layout.css', '/static/css/shaders.css',
  '/static/css/components/buttons.css', '/static/css/components/cards.css', '/static/css/components/badges.css',
  '/static/css/components/tables.css', '/static/css/components/forms.css', '/static/css/components/command.css',
  '/static/css/motion/transitions.css', '/static/css/motion/animations.css',
  '/static/js/core/api.js', '/static/js/core/state.js', '/static/js/core/i18n.js', '/static/js/core/a11y.js',
  '/static/js/core/router.js', '/static/js/core/pwa/db.js', '/static/js/core/pwa/sync.js',
];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(SHELL).catch(function () {}); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener('fetch', function (e) {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Never cache live discovery — quota truth.
  if (url.pathname === '/api/jobs') return;

  // Saved batches: stale-while-revalidate so offline still shows last jobs.
  if (url.pathname === '/api/batches' || url.pathname.indexOf('/api/batch/') === 0) {
    e.respondWith(caches.open(CACHE).then(function (c) {
      return c.match(req).then(function (cached) {
        const net = fetch(req).then(function (res) { if (res.ok) c.put(req, res.clone()); return res; }).catch(function () { return cached; });
        return cached || net;
      });
    }));
    return;
  }

  // Navigations: network first, fall back to offline shell.
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).catch(function () { return caches.match('/').then(function (r) { return r || caches.match('/offline.html'); }); }));
    return;
  }

  // Static assets: cache-first.
  if (url.pathname.indexOf('/static/') === 0) {
    e.respondWith(caches.match(req).then(function (c) { return c || fetch(req).then(function (res) { const copy = res.clone(); caches.open(CACHE).then(function (cc) { cc.put(req, copy); }); return res; }); }));
  }
});
