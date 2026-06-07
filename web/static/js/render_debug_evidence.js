async function loadDebugEvidence() {
    const container = document.getElementById('debug-container');
    container.innerHTML = '<div class="chart-fallback">Loading debug evidence...</div>';
    
    // We don't have a distinct endpoint for this in API_URLS yet, but we rely on pipeline state or jobs data.
    // For S10-C, we assume no data is passed globally yet and we must handle the empty state honestly.
    
    container.innerHTML = `
        <div class="chart-fallback">
            Debug Evidence is currently unavailable.
            <br><br>
            <strong>Backend Gap:</strong> The system does not yet supply the granular 15-field evidence drawer arrays (raw_title, rejection_reasons, budget_cost, query_seed, etc.).
        </div>
    `;
}

function renderEvidence(data, type) {
    const container = document.getElementById('evidence-content');
    if (!data) {
        container.innerHTML = '<div class="chart-fallback">No evidence data available for this selection.</div>';
        return;
    }

    const title = UI.safeField(data.title ?? data.name ?? data.restaurant_name, 'Unknown');
    const comp = UI.safeField(data.company, 'Unknown Company');

    let html = `
        <div style="margin-bottom: var(--space-md);">
            <h4 style="font-size: 1.2rem; font-weight: 700; color: var(--accent);">${UI.escape(title)}</h4>
            <p style="color: var(--muted);">${UI.escape(comp)}</p>
        </div>
        
        <div class="evidence-grid" style="display: grid; gap: var(--space-md); font-size: 0.85rem;">
    `;

    // Mandatory fields per Doc 5
    const fields = [
        { label: 'Raw Title', key: 'raw_title' },
        { label: 'Normalized Title', key: 'normalized_title' },
        { label: 'Source', key: 'source' },
        { label: 'Provider ID', key: 'provider_id' },
        { label: 'Industry Scores', key: 'industry_scores' },
        { label: 'Status', key: 'status' },
        { label: 'Rejection Reasons', key: 'rejection_reasons' },
        { label: 'Dedupe Key', key: 'dedupe_key' },
        { label: 'Place Resolution', key: 'place_resolution' },
        { label: 'Review Score', key: 'review_score' },
        { label: 'Match Score', key: 'match_score' },
        { label: 'Budget Cost', key: 'budget_cost' },
        { label: 'Query Seed', key: 'query_seed' },
        { label: 'Discovery Mode', key: 'discovery_mode' },
        { label: 'Timestamp', key: 'timestamp' }
    ];

    fields.forEach(f => {
        const val = data[f.key];
        let displayVal = UI.safeField(data, f.key, 'Unavailable');
        
        if (f.key === 'industry_scores' && typeof val === 'object' && val !== null) {
            displayVal = JSON.stringify(val);
        } else if (f.key === 'rejection_reasons' && Array.isArray(val)) {
            displayVal = val.length > 0 ? val.map(r => `<span class="badge badge-live">${UI.escape(r)}</span>`).join(' ') : 'None';
        }

        html += `
            <div class="evidence-item" style="border-bottom: 1px solid var(--border); padding-bottom: var(--space-xs);">
                <div style="color: var(--muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px;">${f.label}</div>
                <div style="margin-top: 2px; word-break: break-all;">${displayVal === 'Unavailable' ? UI.renderUnavailable() : UI.escape(displayVal)}</div>
            </div>
        `;
    });

    html += `</div>`;
    
    // Add raw JSON for transparency (bottom)
    html += `
        <details style="margin-top: var(--space-xl); font-size: 0.75rem;">
            <summary style="cursor: pointer; color: var(--muted);">View Raw Data</summary>
            <pre style="background: rgba(0,0,0,0.2); padding: var(--space-sm); border-radius: var(--radius-sm); margin-top: var(--space-sm); overflow-x: auto;">${UI.escape(JSON.stringify(data, null, 2))}</pre>
        </details>
    `;

    container.innerHTML = html;
}