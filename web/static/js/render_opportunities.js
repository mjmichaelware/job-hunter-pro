async function loadOpportunities() {
    const container = document.getElementById('opportunities-container');
    container.innerHTML = '<div class="chart-fallback">Scanning Google Places opportunities...</div>';
    const data = await safeFetch(API_URLS.opportunities);
    AppState.cachedData.opportunities = data;
    renderOpportunitiesList(data);
}

function renderOpportunitiesList(data) {
    const container = document.getElementById('opportunities-container');
    if (UI.isPlaceholder(data)) {
        container.innerHTML = '<div class="chart-fallback">Opportunities endpoint is currently a placeholder (Backend gap). No local business radar data available.</div>';
        return;
    }

    const opps = UI.getArray(data, 'opportunities', 'data');
    if (opps.length === 0) {
        container.innerHTML = '<div class="chart-fallback">No opportunities loaded or matched current filters.</div>';
        return;
    }

    let filtered = opps.filter(o => {
        if (AppState.filters.industry && o.industry !== AppState.filters.industry) return false;
        if (AppState.filters.minRating && o.rating < AppState.filters.minRating) return false;
        return true;
    });

    if (filtered.length === 0) {
        container.innerHTML = '<div class="chart-fallback">No opportunities match current filters.</div>';
        return;
    }

    container.innerHTML = filtered.map(o => {
        const name = UI.safeField(o.name ?? o.restaurant_name, 'Unknown Business');
        const addr = UI.safeField(o.address ?? o.resolved_address, 'Address Unavailable');
        const rating = UI.safeField(o.rating, 'N/A');
        
        return `
        <div class="card" style="margin-bottom:var(--space-sm); display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h5 style="font-weight:600;">${name}</h5>
                <p style="font-size:0.8rem; color:var(--muted);">${addr}</p>
            </div>
            <div style="text-align:right;">
                <span class="badge badge-safe">Rating: ${rating}</span>
            </div>
        </div>`;
    }).join('');
}