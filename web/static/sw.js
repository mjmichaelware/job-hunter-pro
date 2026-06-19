/* sw.js — NO-STALE network-only worker. Opening the app must never show a cached
   version: every HTML/CSS/JS/API request goes to the network while online. The
   ONLY thing cached is the static /offline.html fallback (not the app), shown when
   a navigation fails because the device is truly offline. /api/jobs is never cached.
   The SW stays registered so the PWA/APK remains installable. */

const OFFLINE_CACHE = 'jhp-offline';

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(OFFLINE_CACHE)
      .then(function (c) { return c.add('/offline.html').catch(function () {}); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  // Purge every cache EXCEPT the tiny offline page so no stale app asset survives.
  e.waitUntil(
    caches.keys()
      .then(function (keys) { return Promise.all(keys.filter(function (k) { return k !== OFFLINE_CACHE; }).map(function (k) { return caches.delete(k); })); })
      .then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  const req = e.request;
  if (req.method !== 'GET') return;

  // Navigations: always network; only on offline failure show the honest offline page.
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).catch(function () { return caches.match('/offline.html'); }));
    return;
  }
  // Subresources (CSS/JS/API/assets): force no-store so neither the SW cache NOR
  // the browser HTTP cache can ever serve a stale asset. Always fresh online.
  e.respondWith(fetch(req, { cache: 'no-store' }).catch(function () { return fetch(req); }));
});
