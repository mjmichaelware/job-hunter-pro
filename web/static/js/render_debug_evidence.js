async function loadDebugEvidence() {
    const container = document.getElementById('debug-container');
    container.innerHTML = '<div class="chart-fallback">Loading pipeline telemetry...</div>';
    
    // In a real S10-H implementation, we might fetch last-run telemetry if SSE is not active.
    // For now, we render the Pipeline Reactor UI in its "Ready / Waiting" state.
    
    const stages = [
        { id: 'discover', label: 'Discovery', icon: '🔍' },
        { id: 'normalize', label: 'Normalization', icon: '📝' },
        { id: 'resolve_place', label: 'Place Resolution', icon: '📍' },
        { id: 'classify', label: 'Classification', icon: '🏷️' },
        { id: 'score', label: 'Scoring', icon: '⚖️' },
        { id: 'filter', label: 'Filtering', icon: '🧹' },
        { id: 'dedupe', label: 'Deduplication', icon: '👯' },
        { id: 'store', label: 'Persistence', icon: '💾' }
    ];

    const rejections = [
        { id: 'not_food_service', label: 'Industry Mismatch' },
        { id: 'outside_radius', label: 'Outside Radius' },
        { id: 'ambiguous_place_resolution', label: 'Ambiguous Place' },
        { id: 'duplicate', label: 'Duplicate' },
        { id: 'budget_guard', label: 'Budget Guard' },
        { id: 'provider_error', label: 'Provider Error' },
        { id: 'missing_source_url', label: 'Missing URL' },
        { id: 'transit_unavailable', label: 'Transit Unavailable' },
        { id: 'low_confidence_fit', label: 'Low Confidence' },
        { id: 'low_rating_cap', label: 'Low Rating Cap' },
        { id: 'place_resolution_unavailable', label: 'Place Gap' }
    ];

    let html = `
        <div class="grid-overview" style="margin-bottom: var(--space-md);">
            <div class="card" style="grid-column: span 2;">
                <h3>Pipeline Stage Reactor</h3>
                <div style="display: flex; flex-wrap: wrap; gap: var(--space-sm); margin-top: var(--space-sm);" aria-live="polite" id="pipeline-aria-live">
                    ${stages.map(s => `
                        <div class="pipeline-stage-chip" id="stage-${s.id}">
                            <span class="stage-icon">${s.icon}</span>
                            <span class="stage-label">${s.label}</span>
                            <span class="stage-count">0</span>
                        </div>
                    `).join('')}
                </div>
                <div style="margin-top: var(--space-md); font-size: 0.8rem; color: var(--muted); border-top: 1px solid var(--border); padding-top: var(--space-sm);">
                    Status: <span id="pipeline-status-text">DISCONNECTED</span>
                    <span style="margin-left: var(--space-md);">Stream: <code>${API_URLS.pipeline_stream}</code></span>
                </div>
            </div>
        </div>

        <div class="grid-overview">
            <div class="card">
                <h3>Shedding Registry (Rejections)</h3>
                <div style="display: flex; flex-direction: column; gap: var(--space-xs); margin-top: var(--space-sm);">
                    ${rejections.map(r => `
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; padding: 4px 8px; background: rgba(0,0,0,0.2); border-radius: 4px;">
                            <span>${r.label}</span>
                            <span class="badge badge-live" id="rej-${r.id}">0</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="card">
                <h3>Real-time Logs</h3>
                <div id="pipeline-logs" style="height: 300px; background: #000; color: #0f0; font-family: monospace; font-size: 0.75rem; padding: 10px; overflow-y: auto; border-radius: 4px;">
                    <div style="color: #888;">> Pipeline reactor initialized.</div>
                    <div style="color: #888;">> Awaiting SSE stream connection...</div>
                    <div style="color: var(--danger);">> [ERROR] Stream endpoint unavailable (404). Rendering static telemetry readiness.</div>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
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
