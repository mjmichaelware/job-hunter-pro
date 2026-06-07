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
        `;
        return;
    }

    const providers = UI.getArray(data, 'providers', 'data');
    if (providers.length === 0) {
        container.innerHTML = '<div class="chart-fallback">No providers configured or found.</div>';
        return;
    }

    container.innerHTML = providers.map(p => {
        const name = UI.safeField(p.label, 'Unknown Provider');
        const type = UI.safeField(p.type, 'Unknown Type');
        const available = p.is_available === true;
        
        return `
        <div class="card">
            <h4>${name}</h4>
            <p style="font-size:0.8rem; color:var(--muted);">${type.toUpperCase()}</p>
            <span class="badge ${available ? 'badge-safe' : 'badge-cached'}">${available ? 'READY' : 'DORMANT'}</span>
        </div>`;
    }).join('');
}
