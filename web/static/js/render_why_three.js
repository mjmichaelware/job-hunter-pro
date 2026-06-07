async function loadWhyThree(){const container=document.getElementById('why-three-container');container.innerHTML='<div class="chart-fallback">Retrieving top candidates...</div>';const data=await safeFetch(API_URLS.why_three);if(!data||!data.top3){container.innerHTML='<div class="chart-fallback">No resonance match results calculated. Run live query or batch ingestion.</div>';return}container.innerHTML=data.top3.map((j,i)=>`
<div class="card" style="margin-bottom:var(--space-md); border:1px solid var(--accent);">
    <div style="display:flex; justify-content:space-between;">
        <h4 style="font-weight:700;">Rank #${i+1}: ${j.title}</h4>
        <span class="badge badge-safe">Match: ${j.resonance_score || 0}%</span>
    </div>
    <p style="font-size:0.9rem; color:var(--muted); margin:4px 0;">Company: ${j.company}</p>
    <div style="background:rgba(0,0,0,0.2); padding:10px; border-radius:4px; margin-top:8px;">
        <h5 style="font-size:0.8rem; text-transform:uppercase; color:var(--accent);">Evidence Matrix & Selection Logic</h5>
        <p style="font-size:0.8rem; margin-top:4px;">${j.why_included || 'No inclusion telemetry details cataloged.'}</p>
    </div>
</div>`).join('')}