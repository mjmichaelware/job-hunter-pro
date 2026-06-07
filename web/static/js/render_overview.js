async function loadOverview() {
    const accepted = document.getElementById('overview-accepted-count');
    const opps = document.getElementById('overview-opp-count');
    const batches = document.getElementById('overview-batch-count');
    const burn = document.getElementById('overview-budget-burn');
    const badge = document.getElementById('system-status-badge');

    // Usage / Budget
    const usage = await safeFetch(API_URLS.usage);
    if (UI.isPlaceholder(usage)) {
        burn.textContent = `Unavailable`;
        badge.className = 'badge badge-cached';
        badge.textContent = 'API GAP';
    } else if (usage) {
        // Handle legacy vs new
        const searchesLeft = usage.total_searches_left ?? (usage.serpapi ? usage.serpapi.searches_left : null);
        const monthly = usage.monthly_usage ?? (usage.serpapi ? usage.serpapi.this_month : null);
        
        burn.textContent = monthly !== null ? `${monthly} spent` : `Unavailable`;
        
        if (searchesLeft !== null) {
            badge.className = searchesLeft > 40 ? 'badge badge-safe' : 'badge badge-budget-guarded';
            badge.textContent = searchesLeft > 40 ? 'SAFE' : 'BUDGET GUARDED';
        } else {
            badge.className = 'badge badge-cached';
            badge.textContent = 'STATUS UNKNOWN';
        }
    } else {
        burn.textContent = `Error`;
        badge.className = 'badge badge-live';
        badge.textContent = 'OFFLINE';
    }

    // Jobs count (Dry Run)
    const jobs = await safeFetch(`${API_URLS.jobs}?dry_run=1`);
    if (UI.isPlaceholder(jobs)) {
        accepted.textContent = 'Unavailable';
    } else if (jobs) {
        const jobsArr = UI.getArray(jobs, 'jobs', 'data');
        accepted.textContent = jobsArr.length;
    } else {
        accepted.textContent = 'Error';
    }

    // Opportunities (Dry Run)
    const rawOpps = await safeFetch(`${API_URLS.opportunities}?dry_run=1`);
    if (UI.isPlaceholder(rawOpps)) {
        opps.textContent = 'Unavailable';
    } else if (rawOpps) {
        const oppsArr = UI.getArray(rawOpps, 'opportunities', 'data');
        opps.textContent = oppsArr.length;
    } else {
        opps.textContent = 'Error';
    }

    // History
    const hist = await safeFetch(API_URLS.history);
    if (UI.isPlaceholder(hist)) {
        batches.textContent = 'Unavailable';
    } else if (hist) {
        const histArr = UI.getArray(hist, 'batches', 'data');
        batches.textContent = histArr.length;
    } else {
        batches.textContent = 'Error';
    }
}