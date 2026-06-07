async function loadJobs() {
    const container = document.getElementById('jobs-container');
    container.innerHTML = '<div class="chart-fallback">Loading live jobs securely...</div>';
    const data = await safeFetch(`${API_URLS.jobs}?dry_run=1`);
    AppState.cachedData.jobs = data;
    renderJobsList(data);
}

function renderJobsList(data) {
    const container = document.getElementById('jobs-container');
    if (UI.isPlaceholder(data)) {
        container.innerHTML = '<div class="chart-fallback">Live Jobs endpoint is currently a placeholder (Backend gap). Run live discovery when ready to spend provider budget, or check API connection.</div>';
        return;
    }

    const jobs = UI.getArray(data, 'jobs', 'data');
    if (jobs.length === 0) {
        container.innerHTML = '<div class="chart-fallback">No live jobs loaded. Run live discovery when ready to spend provider budget.</div>';
        return;
    }

    let filtered = jobs.filter(j => {
        if (AppState.filters.industry && j.industry !== AppState.filters.industry) return false;
        
        // Handle legacy radius_miles fallback
        const radius = j.haversine_radius_miles ?? j.radius_miles ?? 999;
        if (radius > AppState.filters.radius) return false;
        
        const score = j.match_score ?? 0;
        if (score < AppState.filters.matchScore) return false;
        
        return true;
    });

    if (filtered.length === 0) {
        container.innerHTML = '<div class="chart-fallback">No live jobs match current filters. Adjust your radius or minimum match score.</div>';
        return;
    }

    container.innerHTML = filtered.map(j => {
        const title = UI.safeField(j.title, 'Untitled Role');
        const comp = UI.safeField(j.company, 'Unknown Company');
        const addr = UI.safeField(j.normalized_address ?? j.address, 'Address Unresolved');
        const ind = UI.escape(j.industry || 'food');
        const score = UI.safeField(j.match_score, 0);
        const radius = j.haversine_radius_miles ?? j.radius_miles;
        const radiusText = radius !== undefined && radius !== null ? Number(radius).toFixed(1) + ' mi' : 'No Dist';
        
        const transitSecs = j.commute_matrix_seconds;
        let transitBadge = 'Unavailable';
        let transitClass = 'badge-cached';
        if (transitSecs !== undefined && transitSecs !== null) {
            transitBadge = Math.round(transitSecs / 60) + ' min';
            transitClass = transitSecs <= 2100 ? 'badge-safe' : 'badge-budget-guarded';
        }

        return `
        <div class="card" style="margin-bottom: var(--space-md); border-left: 4px solid var(--accent-${ind});">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <h4 style="font-size:1.1rem; font-weight:700;">${title}</h4>
                    <p style="color:var(--muted); font-size:0.9rem;">${comp} &bull; ${addr}</p>
                </div>
                <div style="text-align:right;">
                    <div class="badge badge-cached">Score: ${score}%</div>
                    <div style="font-size:0.75rem; color:var(--muted); margin-top:4px;">${radiusText}</div>
                </div>
            </div>
            <div style="margin-top:var(--space-sm); font-size:0.85rem;">
                <span class="badge ${transitClass}">Transit: ${transitBadge}</span>
            </div>
        </div>`;
    }).join('');
}