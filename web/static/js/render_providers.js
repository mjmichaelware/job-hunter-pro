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
        const disabled = p.disabled_by_policy === true;

        let badgeClass = 'badge-cached';
        let badgeText = 'DORMANT';
        if (disabled) { badgeClass = 'badge-budget-guarded'; badgeText = 'DISABLED'; }
        else if (available) { badgeClass = 'badge-safe'; badgeText = 'READY'; }

        const reason = disabled && p.reason
            ? `<p style="font-size:0.75rem; color:var(--warning); margin-top:var(--space-xs);">${UI.safeField(p.reason, '')}</p>`
            : '';

        return `
        <div class="card">
            <h4>${name}</h4>
            <p style="font-size:0.8rem; color:var(--muted);">${type.toUpperCase()}</p>
            <span class="badge ${badgeClass}">${badgeText}</span>
            ${reason}
        </div>`;
    }).join('');
}
