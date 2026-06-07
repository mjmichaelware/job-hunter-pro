async function loadProviders() {
    const container = document.getElementById('providers-container');
    container.innerHTML = '<div class="chart-fallback">Loading providers data...</div>';
    
    const data = await safeFetch(API_URLS.providers);
    
    if (UI.isPlaceholder(data)) {
        container.innerHTML = `
            <div class="chart-fallback">
                Providers endpoint is currently a placeholder (Backend gap). 
                Rendering offline/not-configured fallback state.
            </div>
            <div class="card" style="opacity: 0.7;">
                <h4>Discovery APIs</h4>
                <span class="badge badge-cached">MISSING KEY</span>
            </div>
            <div class="card" style="opacity: 0.7;">
                <h4>Reasoning APIs (LLM)</h4>
                <span class="badge badge-cached">MISSING KEY</span>
            </div>
        `;
        return;
    }

    const providers = UI.getArray(data, 'providers', 'data');
    if (providers.length === 0) {
        container.innerHTML = '<div class="chart-fallback">No providers configured or found.</div>';
        return;
    }

    container.innerHTML = providers.map(p => {
        const name = UI.safeField(p.name, 'Unknown Provider');
        const type = UI.safeField(p.type, 'Unknown Type');
        const status = UI.safeField(p.status, 'unavailable');
        
        return `
        <div class="card">
            <h4>${name}</h4>
            <p>Type: ${type}</p>
            <span class="badge badge-${status === 'active' || status === 'safe' ? 'safe' : 'cached'}">${status.toUpperCase()}</span>
        </div>`;
    }).join('');
}