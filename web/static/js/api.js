/* api.js — safe fetch helpers. No hardcoded data. No live discovery on boot. */

// Escape HTML entities
function esc(v) {
  return String(v == null ? '' : v)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// Pick first non-null/empty value from an object by priority key list
function pick(obj, keys, fallback) {
  for (const k of keys) {
    const v = obj ? obj[k] : undefined;
    if (v !== undefined && v !== null && v !== '') return v;
  }
  return fallback;
}

// Extract an array from a payload by trying multiple key names
function arr(payload, keys) {
  for (const k of keys) {
    if (payload && Array.isArray(payload[k])) return payload[k];
  }
  return [];
}

// Validate a URL — returns clean string or empty
function href(v) {
  const s = String(v || '').trim();
  return (s.startsWith('http://') || s.startsWith('https://')) ? s : '';
}

// Build a query string from a params object (omits null/undefined/empty)
function buildQuery(params) {
  const parts = [];
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && v !== '') {
      parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(v));
    }
  }
  return parts.length ? '?' + parts.join('&') : '';
}

// Safe fetch: returns parsed JSON or null on any error
async function safeFetch(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) {
      console.warn('[api] HTTP ' + res.status + ' from ' + url);
      return null;
    }
    return await res.json();
  } catch (err) {
    console.warn('[api] fetch error ' + url + ':', err.message);
    return null;
  }
}

// Fresh live discovery — SPENDS quota. Called only on explicit user action.
async function fetchJobsLive(filters) {
  const params = Object.assign({ dry_run: 0 }, filters || {});
  return safeFetch('/api/jobs' + buildQuery(params));
}

// Dry-run query plan — does NOT spend discovery budget.
async function fetchJobsDryRun(filters) {
  const params = Object.assign({ dry_run: 1 }, filters || {});
  return safeFetch('/api/jobs' + buildQuery(params));
}
