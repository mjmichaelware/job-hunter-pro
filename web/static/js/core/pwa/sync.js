/* core/pwa/sync.js — write-through cache + offline read.
   On a successful view load we persist the payload; when offline we serve it back.
   Honest: an offline render is badged "cached" by the view, never passed as live. */

const JHP_SYNC = {
  online: function () { return navigator.onLine !== false; },

  // Cache a view's real payload for offline reuse.
  remember: function (viewId, payload) {
    if (payload == null) return;
    AppState.cache[viewId] = payload;
    if (typeof JHP_DB !== 'undefined') JHP_DB.putView(viewId, payload);
  },

  // Recall a cached payload (memory first, then IndexedDB).
  recall: function (viewId) {
    if (AppState.cache[viewId] != null) return Promise.resolve(AppState.cache[viewId]);
    if (typeof JHP_DB !== 'undefined') return JHP_DB.getView(viewId);
    return Promise.resolve(null);
  },
};

// Surface connectivity changes to the health strip honestly.
window.addEventListener('offline', function () {
  const strip = document.getElementById('health-strip');
  if (strip) strip.innerHTML = '<span class="badge badge-cached">offline — cached</span>';
  if (typeof announce === 'function') announce('You are offline. Showing cached data.');
});
window.addEventListener('online', function () {
  if (typeof renderHealth === 'function') renderHealth();
});
