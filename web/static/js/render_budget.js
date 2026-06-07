async function loadBudget() {
    const container = document.getElementById('budget-left');
    const safeIndicator = document.getElementById('budget-safe-indicator');
    const dryRunOutput = document.getElementById('dry-run-output');
    
    container.textContent = 'Loading budget data...';
    dryRunOutput.style.display = 'none';

    // Fetch usage data
    const usage = await safeFetch(API_URLS.usage);
    
    if (UI.isPlaceholder(usage)) {
        container.textContent = 'Data Unavailable (API Gap)';
        safeIndicator.textContent = 'UNAVAILABLE';
        safeIndicator.className = 'badge badge-cached';
    } else if (usage) {
        const searchesLeft = usage.total_searches_left ?? (usage.serpapi ? usage.serpapi.searches_left : null);
        
        if (searchesLeft !== null) {
            container.textContent = `${searchesLeft} searches left`;
            safeIndicator.textContent = searchesLeft > 40 ? 'ACTIVE' : 'BUDGET GUARDED';
            safeIndicator.className = searchesLeft > 40 ? 'badge badge-safe' : 'badge badge-budget-guarded';
        } else {
            container.textContent = 'Usage tracking unavailable';
            safeIndicator.textContent = 'UNKNOWN';
            safeIndicator.className = 'badge badge-cached';
        }
    } else {
        container.textContent = 'N/A';
        safeIndicator.textContent = 'ERROR';
        safeIndicator.className = 'badge badge-live';
    }

    // Dry Run Button Logic
    const dryRunBtn = document.getElementById('dry-run-plan-btn');
    if (dryRunBtn) {
        dryRunBtn.onclick = async () => {
            dryRunOutput.style.display = 'block';
            dryRunOutput.textContent = 'Generating dry-run plan...';
            const dryRunData = await safeFetch(`${API_URLS.jobs}?dry_run=1&full_report=true`);
            
            if (UI.isPlaceholder(dryRunData)) {
                dryRunOutput.textContent = 'Backend GAP: Jobs endpoint returned a placeholder. Cannot generate dry-run execution plan.';
            } else if (dryRunData && dryRunData.plan) {
                dryRunOutput.textContent = JSON.stringify(dryRunData.plan, null, 2);
            } else if (dryRunData && dryRunData.dry_run) {
                // Legacy schema fallback
                dryRunOutput.textContent = 'Legacy dry run mode detected:\n' + JSON.stringify(dryRunData, null, 2);
            } else {
                dryRunOutput.textContent = 'Failed to generate dry-run plan or no plan available.';
            }
        };
    }
}