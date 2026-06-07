const API_URLS = Object.freeze({
  health: '/api/health',
  usage: '/api/usage',
  jobs: '/api/jobs',
  opportunities: '/api/opportunities',
  history: '/api/history',
  providers: '/api/providers',
  industries: '/api/industries',
  applications: '/api/applications',
  why_three: '/api/why-three'
});

async function safeFetch(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP_${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(`Fetch error [${url}]:`, err);
    return null;
  }
}

function buildQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  const text = query.toString();
  return text ? `?${text}` : '';
}

async function fetchJobsDryRun(params = {}) {
  return safeFetch(`/api/jobs${buildQuery({ ...params, dry_run: 1 })}`);
}

async function fetchJobsLive(params = {}) {
  return safeFetch(`/api/jobs${buildQuery({ ...params, dry_run: 0 })}`);
}

window.UI = window.UI || {};

UI.isPlaceholder = function isPlaceholder(payload) {
  if (!payload || typeof payload !== 'object') return false;
  const message = String(payload.message || payload.detail || '').toLowerCase();
  return message.includes('placeholder') || message.includes('not implemented');
};

UI.getArray = function getArray(payload, keys = []) {
  if (!payload || UI.isPlaceholder(payload)) return [];

  if (Array.isArray(payload)) return payload;

  for (const key of keys) {
    const value = payload[key];
    if (Array.isArray(value)) return value;
  }

  const fallbackKeys = [
    'data',
    'jobs',
    'opportunities',
    'batches',
    'providers',
    'industries',
    'applications',
    'top3',
    'results',
    'items'
  ];

  for (const key of fallbackKeys) {
    const value = payload[key];
    if (Array.isArray(value)) return value;
  }

  return [];
};

UI.safeField = function safeField(obj, keys, fallback = 'Unavailable') {
  if (!obj || typeof obj !== 'object') return fallback;

  const keyList = Array.isArray(keys) ? keys : [keys];

  for (const key of keyList) {
    const value = obj[key];
    if (value !== undefined && value !== null && value !== '') return value;
  }

  return fallback;
};

UI.escape = function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
};

UI.renderUnavailable = function renderUnavailable(label = 'Unavailable') {
  return `<span class="muted">${UI.escape(label)}</span>`;
};
