async function loadJobs(){const container=document.getElementById('jobs-container');container.innerHTML='<div class="chart-fallback">Loading live jobs securely...</div>';const data=await safeFetch(`${API_URLS.jobs}?dry_run=1`);AppState.cachedData.jobs=data;renderJobsList(data)}function renderJobsList(data){const container=document.getElementById('jobs-container');if(!data||!data.jobs||data.jobs.length===0){container.innerHTML='<div class="chart-fallback">No live jobs loaded. Run live discovery when ready to spend provider budget.</div>';return}let filtered=data.jobs.filter(j=>{if(AppState.filters.industry&&j.industry!==AppState.filters.industry)return false;if(j.haversine_radius_miles>AppState.filters.radius)return false;if(j.match_score<AppState.filters.matchScore)return false;return true});if(filtered.length===0){container.innerHTML='<div class="chart-fallback">No live jobs match current filters. Adjust your radius or minimum match score.</div>';return}container.innerHTML=filtered.map(j=>`
<div class="card" style="margin-bottom: var(--space-md); border-left: 4px solid var(--accent-${j.industry||'food'});">
    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
            <h4 style="font-size:1.1rem; font-weight:700;">${j.title}</h4>
            <p style="color:var(--muted); font-size:0.9rem;">${j.company} &bull; ${j.normalized_address||'Address Unresolved'}</p>
        </div>
        <div style="text-align:right;">
            <div class="badge badge-cached">Score: ${j.match_score || 0}%</div>
            <div style="font-size:0.75rem; color:var(--muted); margin-top:4px;">${j.haversine_radius_miles ? j.haversine_radius_miles.toFixed(1)+' mi' : 'No Dist'}</div>
        </div>
    </div>
    <div style="margin-top:var(--space-sm); font-size:0.85rem;">
        <span class="badge ${j.commute_matrix_seconds && j.commute_matrix_seconds <= 2100 ? 'badge-safe':'badge-budget-guarded'}">
            Transit: ${j.commute_matrix_seconds ? Math.round(j.commute_matrix_seconds/60)+' min' : 'Unavailable'}
        </span>
    </div>
</div>`).join('')}
