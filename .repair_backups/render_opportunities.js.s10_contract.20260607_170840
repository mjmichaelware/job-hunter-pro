async function loadOpportunities() {
    const container = document.getElementById('opportunities-container');
    const originAddr = document.getElementById('geo-origin-addr');
    const markovContainer = document.getElementById('markov-radar-container');
    
    container.innerHTML = '<div class="chart-fallback">Scanning Google Places opportunities...</div>';
    
    const data = await safeFetch(API_URLS.opportunities);
    AppState.cachedData.opportunities = data;
    
    // Update Geo Origin from Health or data if available
    const health = AppState.cachedData.health;
    if (health && health.origin_address) {
        originAddr.textContent = health.origin_address;
        originAddr.className = 'badge badge-safe';
    } else {
        originAddr.textContent = 'Backend Gap';
        originAddr.className = 'badge badge-cached';
    }

    renderOpportunitiesList(data);
    renderMarkovRadar(data);
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
        const reviews = UI.safeField(o.user_ratings_total ?? o.review_count, '0');
        const dist = o.distance_miles ?? o.radius_miles;
        const distText = dist ? dist.toFixed(2) + ' mi' : 'No Dist';

        return `
        <div class="card clickable-card" data-id="${UI.escape(o.place_id || o.id || '')}" data-type="opportunity" style="margin-bottom:var(--space-sm); display:flex; justify-content:space-between; align-items:center; cursor: pointer;" role="button" tabindex="0">
            <div style="pointer-events: none;">
                <h5 style="font-weight:600;">${name}</h5>
                <p style="font-size:0.8rem; color:var(--muted);">${addr}</p>
                <div style="font-size:0.75rem; color:var(--accent); margin-top:4px;">
                    Distance: ${distText} &bull; ${reviews} reviews
                </div>
            </div>
            <div style="text-align:right; pointer-events: none;">
                <span class="badge badge-safe">Rating: ${rating}</span>
            </div>
        </div>`;
    }).join('');
}

function renderMarkovRadar(data) {
    const markovContainer = document.getElementById('markov-radar-container');
    if (!data || !data.markov_predictions || data.markov_predictions.length === 0) {
        markovContainer.innerHTML = '<div class="chart-fallback">Markov Radar (Beta) offline. No prediction telemetry returned from backend.</div>';
        return;
    }

    markovContainer.innerHTML = `
        <div style="display: grid; gap: 8px;">
            ${data.markov_predictions.map(p => `
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; padding: 6px; background: rgba(187,134,252,0.1); border: 1px dashed var(--accent); border-radius: 4px;">
                    <span>${UI.escape(p.category)}</span>
                    <span style="color: var(--accent); font-weight: bold;">${(p.vacancy_probability * 100).toFixed(0)}% Vacancy</span>
                </div>
            `).join('')}
        </div>
        <div style="font-size: 0.65rem; color: var(--muted); margin-top: 8px; text-align: center;">
            Beta: Statistical vacancy prediction based on industry turnover. Not a live job.
        </div>
    `;
}