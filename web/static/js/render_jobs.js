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
        // Industry
        if (AppState.filters.industry && j.industry !== AppState.filters.industry) return false;
        
        // Mode
        if (AppState.filters.mode && j.discovery_mode !== AppState.filters.mode) return false;

        // Provider
        if (AppState.filters.provider && j.provider_id !== AppState.filters.provider) return false;

        // Status
        if (AppState.filters.status) {
            if (AppState.filters.status === 'new' && j.application_status) return false;
            if (AppState.filters.status === 'accepted' && j.status !== 'accepted') return false;
            if (AppState.filters.status === 'rejected' && j.status !== 'rejected') return false;
        }

        // Radius
        const radius = j.haversine_radius_miles ?? j.radius_miles ?? 999;
        if (radius > AppState.filters.radius) return false;
        
        // Match Score
        const score = j.match_score ?? 0;
        if (score < AppState.filters.matchScore) return false;
        
        // Max Walk
        if (j.walk_duration_minutes && j.walk_duration_minutes > AppState.filters.maxWalk) return false;

        // Max Transit
        const transitMin = j.commute_matrix_seconds ? j.commute_matrix_seconds / 60 : null;
        if (transitMin && transitMin > AppState.filters.maxTransit) return false;

        // Min Rating
        if (j.rating && j.rating < AppState.filters.minRating) return false;

        // Min Review Score
        if (j.review_score && j.review_score < AppState.filters.minReview) return false;

        // Job Type
        if (AppState.filters.jobType && j.job_type !== AppState.filters.jobType) return false;

        // Pay Hint
        if (AppState.filters.payHint && j.pay_hint !== AppState.filters.payHint) return false;

        // Remote/Onsite
        if (AppState.filters.remoteOnsite && j.remote_onsite !== AppState.filters.remoteOnsite) return false;

        // Batch ID
        if (AppState.filters.batchId && j.batch_id && !j.batch_id.includes(AppState.filters.batchId)) return false;

        // Rejection Reason
        if (AppState.filters.rejectionReason && j.rejection_reason !== AppState.filters.rejectionReason) return false;

        // Confidence
        if (AppState.filters.confidence && j.classification_confidence && (j.classification_confidence * 100) < AppState.filters.confidence) return false;

        // Place Status
        if (AppState.filters.placeStatus && j.place_status !== AppState.filters.placeStatus) return false;

        // Application State
        if (AppState.filters.applicationState && j.application_status !== AppState.filters.applicationState) return false;

        // Duplicate State
        if (AppState.filters.duplicateState) {
            if (AppState.filters.duplicateState === 'duplicate' && !j.is_duplicate) return false;
            if (AppState.filters.duplicateState === 'canonical' && j.is_duplicate) return false;
        }

        return true;
    });

    // Sorting
    filtered.sort((a, b) => {
        if (AppState.filters.sort === 'score') {
            return (b.match_score || 0) - (a.match_score || 0);
        } else if (AppState.filters.sort === 'distance') {
            const distA = a.haversine_radius_miles ?? a.radius_miles ?? 999;
            const distB = b.haversine_radius_miles ?? b.radius_miles ?? 999;
            return distA - distB;
        } else {
            // Newest (default)
            const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
            const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
            return timeB - timeA;
        }
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