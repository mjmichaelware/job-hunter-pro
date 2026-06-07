async function loadBudget(){const container=document.getElementById('budget-left');const dryRunOutput=document.getElementById('dry-run-output');const triggerDiscoveryBtn=document.getElementById('trigger-discovery-btn');
    container.textContent = 'Loading budget data...';
    dryRunOutput.style.display = 'none';

    // Fetch usage data
    const usage = await safeFetch(API_URLS.usage);
    if (usage) {
        container.textContent = `${usage.total_searches_left || 0} searches left`;
        document.getElementById('budget-safe-indicator').textContent = usage.total_searches_left > 40 ? 'ACTIVE' : 'BUDGET GUARDED';
        document.getElementById('budget-safe-indicator').className = usage.total_searches_left > 40 ? 'badge badge-safe' : 'badge badge-budget-guarded';
    } else {
        container.textContent = 'N/A';
        document.getElementById('budget-safe-indicator').textContent = 'UNAVAILABLE';
        document.getElementById('budget-safe-indicator').className = 'badge badge-live'; // Indicate an error state
    }

    // Dry Run Button Logic
    document.getElementById('dry-run-plan-btn').onclick = async () => {
        dryRunOutput.style.display = 'block';
        dryRunOutput.textContent = 'Generating dry-run plan...';
        const dryRunData = await safeFetch(`${API_URLS.jobs}?dry_run=1&full_report=true`); // Assuming full_report for more detail
        if (dryRunData && dryRunData.plan) {
            dryRunOutput.textContent = JSON.stringify(dryRunData.plan, null, 2);
        } else {
            dryRunOutput.textContent = 'Failed to generate dry-run plan or no plan available.';
        }
    };

    // Live Discovery Button Logic (already in state_sync.js but re-adding here for completeness related to budget)
    // The main event listener for this is in state_sync.js, so ensure this doesn't duplicate
    if (triggerDiscoveryBtn) {
        triggerDiscoveryBtn.onclick = async () => {
            if (!confirm('Execute Live Discovery? This query triggers search API calls and consumes budget quota.')) return;
            const jobsContainer = document.getElementById('jobs-container');
            jobsContainer.innerHTML = '<div class="chart-fallback">Running Live Discovery...</div>';
            const data = await safeFetch(`${API_URLS.jobs}`);
            AppState.cachedData.jobs = data;
            if (typeof renderJobsList === 'function') renderJobsList(data);
            if (typeof loadOverview === 'function') await loadOverview(); // Refresh overview for budget
        };
    }
}