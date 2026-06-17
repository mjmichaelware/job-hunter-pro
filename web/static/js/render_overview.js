
function countArrayPayload(payload, keys) {
  if (!payload || typeof payload !== 'object') return 0;
  for (const key of keys) {
    const value = payload[key];
    if (Array.isArray(value)) return value.length;
    if (typeof value === 'number') return value;
  }
  if (payload.data) {
    if (Array.isArray(payload.data)) return payload.data.length;
    if (typeof payload.data === 'object') {
      for (const key of keys) {
        const value = payload.data[key];
        if (Array.isArray(value)) return value.length;
        if (typeof value === 'number') return value;
      }
    }
  }
  return 0;
}

function pickUsageLeft(usage) {
  if (!usage || typeof usage !== 'object') return null;
  if (usage.total_searches_left !== undefined) return usage.total_searches_left;
  if (usage.serpapi?.total_searches_left !== undefined) return usage.serpapi.total_searches_left;
  if (usage.serpapi?.searches_left !== undefined) return usage.serpapi.searches_left;
  if (usage.serpapi?.remaining !== undefined) return usage.serpapi.remaining;
  return null;
}


async function loadOverview() {
    const acceptedCount = document.getElementById('overview-accepted-count');
    const oppCount = document.getElementById('overview-opp-count');
    const batchCount = document.getElementById('overview-batch-count');
    const budgetBurn = document.getElementById('overview-budget-burn');
    const systemStatus = document.getElementById('system-status-badge');

    // Safe status endpoints. Do NOT re-fetch jobs here: reuse whatever the
    // Live Jobs tab already discovered so we never clobber the live cache with a
    // dry-run (which would force another paid run on the next visit).
    const [health, usage, opps, history] = await Promise.all([
        safeFetch(API_URLS.health),
        safeFetch(API_URLS.usage),
        safeFetch(API_URLS.opportunities),
        safeFetch(API_URLS.history)
    ]);

    // Update global state
    AppState.cachedData.health = health;
    AppState.cachedData.usage = usage;
    AppState.cachedData.opportunities = opps;
    AppState.cachedData.history = history;

    // Render Stats — real accepted count from the live run, if one has happened.
    if (acceptedCount) {
        const jobs = AppState.cachedData.jobs;
        if (jobs && !jobs.dry_run) {
            acceptedCount.textContent = jobs.count ?? jobs.accepted_count ?? UI.getArray(jobs).length ?? '0';
        } else {
            acceptedCount.textContent = '—';
        }
    }

    if (oppCount) {
        const items = UI.getArray(opps);
        oppCount.textContent = items.length || '0';
    }

    if (batchCount) {
        const items = UI.getArray(history);
        batchCount.textContent = items.length || '0';
    }

    if (budgetBurn) {
        if (UI.isPlaceholder(usage)) {
            budgetBurn.innerHTML = UI.renderUnavailable('Gap');
        } else if (usage) {
            const burn = usage.budget_efficiency ?? usage.burn_rate ?? null;
            budgetBurn.textContent = burn !== null ? `${(burn * 100).toFixed(1)}%` : '100%';
        } else {
            budgetBurn.textContent = 'N/A';
        }
    }

    // Update System Status Badge
    if (systemStatus) {
        if (health && health.status === 'ok') {
            systemStatus.textContent = 'SAFE';
            systemStatus.className = 'badge badge-safe';
        } else {
            systemStatus.textContent = 'UNSTABLE';
            systemStatus.className = 'badge badge-live';
        }
    }
}
