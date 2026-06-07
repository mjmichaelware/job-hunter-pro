const API_URLS = Object.freeze({
  health: '/api/health',
  usage: '/api/usage',
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
