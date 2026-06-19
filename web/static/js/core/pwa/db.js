/* core/pwa/db.js — IndexedDB store for saved batches + view snapshots.
   Enables offline dignity: the app re-renders from this cache with zero network. */

const JHP_DB = (function () {
  const DB_NAME = 'jhp';
  const DB_VERSION = 1;
  let dbp = null;

  function open() {
    if (dbp) return dbp;
    dbp = new Promise(function (resolve, reject) {
      if (!('indexedDB' in window)) { reject(new Error('no-indexeddb')); return; }
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = function () {
        const db = req.result;
        if (!db.objectStoreNames.contains('batches')) db.createObjectStore('batches', { keyPath: 'id' });
        if (!db.objectStoreNames.contains('views')) db.createObjectStore('views', { keyPath: 'id' });
      };
      req.onsuccess = function () { resolve(req.result); };
      req.onerror = function () { reject(req.error); };
    });
    return dbp;
  }

  function tx(store, mode, fn) {
    return open().then(function (db) {
      return new Promise(function (resolve, reject) {
        const t = db.transaction(store, mode);
        const os = t.objectStore(store);
        const out = fn(os);
        t.oncomplete = function () { resolve(out && out.result !== undefined ? out.result : out); };
        t.onerror = function () { reject(t.error); };
      });
    });
  }

  return {
    putView: function (id, payload) {
      return tx('views', 'readwrite', function (os) { os.put({ id: id, payload: payload, ts: Date.now() }); })
        .catch(function () {});
    },
    getView: function (id) {
      return tx('views', 'readonly', function (os) { return os.get(id); })
        .then(function (r) { return r ? r.payload : null; })
        .catch(function () { return null; });
    },
    putBatch: function (id, jobs) {
      return tx('batches', 'readwrite', function (os) { os.put({ id: id, jobs: jobs, ts: Date.now() }); })
        .catch(function () {});
    },
    listBatches: function () {
      return tx('batches', 'readonly', function (os) { return os.getAll(); })
        .then(function (r) { return r || []; })
        .catch(function () { return []; });
    },
  };
})();
