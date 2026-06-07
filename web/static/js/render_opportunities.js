async function loadOpportunities(){const container=document.getElementById('opportunities-container');container.innerHTML='<div class="chart-fallback">Scanning Google Places opportunities...</div>';const data=await safeFetch(API_URLS.opportunities);AppState.cachedData.opportunities=data;renderOpportunitiesList(data)}function renderOpportunitiesList(data){const container=document.getElementById('opportunities-container');if(!data||!data.opportunities||data.opportunities.length===0){container.innerHTML='<div class="chart-fallback">No opportunities loaded or matched current filters.</div>';return}let filtered=data.opportunities.filter(o=>{if(AppState.filters.industry&&o.industry!==AppState.filters.industry)return false;return true});if(filtered.length===0){container.innerHTML='<div class="chart-fallback">No opportunities match current filters.</div>';return}container.innerHTML=filtered.map(o=>`
<div class="card" style="margin-bottom:var(--space-sm); display:flex; justify-content:space-between; align-items:center;">
    <div>
        <h5 style="font-weight:600;">${o.name}</h5>
        <p style="font-size:0.8rem; color:var(--muted);">${o.address}</p>
    </div>
    <div style="text-align:right;">
        <span class="badge badge-safe">Rating: ${o.rating||'N/A'}</span>
    </div>
</div>`).join('')}
