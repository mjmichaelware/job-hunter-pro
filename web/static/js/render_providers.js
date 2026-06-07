async function loadProviders(){const container=document.getElementById('providers-container');container.innerHTML='<div class="chart-fallback">Loading providers data...</div>';
    // Implementation note: Render providers only from returned backend data based on API_URLS.providers
    console.log('loadProviders function called.');
    const data = await safeFetch(API_URLS.providers);
    if (!data || !data.providers || data.providers.length === 0) {
        container.innerHTML = '<div class="chart-fallback">No providers configured or found.</div>';
        return;
    }
    // Example rendering:
    container.innerHTML = data.providers.map(p => `
        <div class="card">
            <h4>${p.name}</h4>
            <p>Type: ${p.type}</p>
            <span class="badge badge-${p.status}">${p.status.toUpperCase()}</span>
        </div>
    `).join('');
}