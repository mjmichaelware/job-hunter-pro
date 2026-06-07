async function loadBudget() {
    const container = document.getElementById('budget-left');
    const safeIndicator = document.getElementById('budget-safe-indicator');
    const monthlyUsage = document.getElementById('budget-monthly-usage');
    const estCost = document.getElementById('budget-est-cost');
    const providerList = document.getElementById('provider-budget-list');
    const dryRunOutput = document.getElementById('dry-run-output');
    
    container.textContent = 'Loading budget data...';
    if (monthlyUsage) monthlyUsage.textContent = 'Loading...';
    if (estCost) estCost.textContent = 'Loading...';
    if (providerList) providerList.innerHTML = '<div class="muted">Loading provider status...</div>';
    dryRunOutput.style.display = 'none';

    // Fetch usage data
    const usage = await safeFetch(API_URLS.usage);
    
    // Determine budget state
    let state = BUDGET_STATES.SAFE;
    if (!usage || UI.isPlaceholder(usage)) {
        state = BUDGET_STATES.PARTIAL;
    } else if (usage.error) {
        state = BUDGET_STATES.FAILED;
    }

    // Update global state
    AppState.budgetState = state;

    // Honest rendering of usage data
    if (UI.isPlaceholder(usage)) {
        container.innerHTML = UI.renderUnavailable('Backend Gap');
        if (monthlyUsage) monthlyUsage.innerHTML = UI.renderUnavailable();
        if (estCost) estCost.innerHTML = UI.renderUnavailable();
        if (providerList) providerList.innerHTML = '<div class="muted">Usage tracking not implemented in backend.</div>';
        
        safeIndicator.textContent = 'UNAVAILABLE';
        safeIndicator.className = 'badge badge-cached';
    } else if (usage) {
        const searchesLeft = usage.total_searches_left ?? (usage.serpapi ? usage.serpapi.searches_left : null);
        const monthly = usage.monthly_usage ?? null;
        const est = usage.estimated_action_cost ?? null;

        if (searchesLeft !== null) {
            container.textContent = `${searchesLeft} searches left`;
            if (searchesLeft <= 10) state = BUDGET_STATES.BLOCKED;
            else if (searchesLeft <= 40) state = BUDGET_STATES.BUDGET_GUARDED;
        } else {
            container.innerHTML = UI.renderUnavailable();
        }

        if (monthly !== null) {
            monthlyUsage.textContent = `$${monthly.toFixed(2)}`;
        } else {
            monthlyUsage.innerHTML = UI.renderUnavailable();
        }

        if (est !== null) {
            estCost.textContent = `$${est.toFixed(2)}`;
        } else {
            estCost.innerHTML = UI.renderUnavailable();
        }

        // Provider breakdown
        if (usage.providers && Array.isArray(usage.providers)) {
            providerList.innerHTML = usage.providers.map(p => `
                <div style="display:flex; justify-content:space-between; margin-bottom:var(--space-xs); font-size:0.85rem;">
                    <span>${UI.escape(p.label)}</span>
                    <span class="badge ${p.status === 'active' ? 'badge-safe' : 'badge-cached'}">${UI.escape(p.status.toUpperCase())}</span>
                </div>
            `).join('');
        } else {
            providerList.innerHTML = '<div class="muted">No provider usage data available.</div>';
        }

        // Update safe indicator based on computed state
        updateSafeIndicator(safeIndicator, state);
    } else {
        container.textContent = 'N/A';
        safeIndicator.textContent = 'ERROR';
        safeIndicator.className = 'badge badge-live';
        if (providerList) providerList.innerHTML = '<div class="muted">Failed to fetch budget data.</div>';
    }

    // Dry Run Button Logic
    const dryRunBtn = document.getElementById('dry-run-plan-btn');
    if (dryRunBtn) {
        dryRunBtn.onclick = async () => {
            dryRunOutput.style.display = 'block';
            dryRunOutput.textContent = 'Generating dry-run plan (Safe: 0 budget impact)...';
            
            // Explicitly set state to dry_run during this action
            const prevState = AppState.budgetState;
            AppState.budgetState = BUDGET_STATES.DRY_RUN;
            
            const dryRunData = await safeFetch(`${API_URLS.jobs}?dry_run=1&full_report=true`);
            
            if (UI.isPlaceholder(dryRunData)) {
                dryRunOutput.textContent = 'Backend GAP: Jobs endpoint returned a placeholder. Cannot generate dry-run execution plan.';
            } else if (dryRunData && dryRunData.plan) {
                dryRunOutput.textContent = JSON.stringify(dryRunData.plan, null, 2);
            } else {
                dryRunOutput.textContent = 'Failed to generate dry-run plan or no plan available.\n' + (dryRunData ? JSON.stringify(dryRunData, null, 2) : '');
            }
            
            AppState.budgetState = prevState;
        };
    }
}

function updateSafeIndicator(el, state) {
    el.textContent = state.toUpperCase().replace('_', ' ');
    switch (state) {
        case BUDGET_STATES.SAFE:
            el.className = 'badge badge-safe';
            break;
        case BUDGET_STATES.BUDGET_GUARDED:
            el.className = 'badge badge-budget-guarded';
            break;
        case BUDGET_STATES.BLOCKED:
            el.className = 'badge badge-live'; // Use live color for warning/danger
            break;
        default:
            el.className = 'badge badge-cached';
            break;
    }
}
