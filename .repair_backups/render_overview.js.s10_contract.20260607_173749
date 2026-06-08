
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

    // Safe Boot: Fetch cached/safe endpoints only
    const [health, usage, jobs, opps, history] = await Promise.all([
        safeFetch(API_URLS.health),
        safeFetch(API_URLS.usage),
        fetchJobsDryRun(), // explicit safe dry-run; no live discovery on boot
        safeFetch(API_URLS.opportunities),
        safeFetch(API_URLS.history)
    ]);

    // Update global state
    AppState.cachedData.health = health;
    AppState.cachedData.usage = usage;
    AppState.cachedData.jobs = jobs;
    AppState.cachedData.opportunities = opps;
    AppState.cachedData.history = history;

    // Render Stats
    if (acceptedCount) {
        const items = UI.getArray(jobs);
        acceptedCount.textContent = items.filter(j => j.status === 'accepted').length || '0';
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
