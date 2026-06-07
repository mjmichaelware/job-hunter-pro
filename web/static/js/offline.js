window.OfflineStore = (function createOfflineStore() {
  const DB_NAME = 'job-hunter-pro-offline';
  const DB_VERSION = 1;
  const STORE_NAME = 'safe_payloads';
  let dbPromise = null;

  function open() {
    if (dbPromise) return dbPromise;

    dbPromise = new Promise((resolve, reject) => {
      if (!('indexedDB' in window)) {
        reject(new Error('IndexedDB unavailable'));
        return;
      }

      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: 'key' });
        }
      };

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error('IndexedDB open failed'));
    });

    return dbPromise;
  }

  async function put(key, payload) {
    const db = await open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      tx.objectStore(STORE_NAME).put({
        key,
        payload,
        cached_at: new Date().toISOString(),
        cache_state: 'cached',
        stale_state: 'fresh'
      });
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error || new Error('IndexedDB write failed'));
    });
  }

  async function get(key) {
    const db = await open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const request = tx.objectStore(STORE_NAME).get(key);
      request.onsuccess = () => {
        const record = request.result || null;
        if (!record) {
          resolve(null);
          return;
        }
        resolve({
          ...record,
          cache_state: 'cached',
          stale_state: 'stale',
          offline_state: 'offline'
        });
      };
      request.onerror = () => reject(request.error || new Error('IndexedDB read failed'));
    });
  }

  open().catch(() => null);

  return { open, put, get };
})();
