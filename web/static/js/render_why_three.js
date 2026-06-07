async function loadWhyThree() {
    const container = document.getElementById('why-three-container');
    container.innerHTML = '<div class="chart-fallback">Retrieving top candidates...</div>';
    
    const data = await safeFetch(API_URLS.why_three);
    AppState.cachedData.whyThree = data;
    
    if (UI.isPlaceholder(data)) {
        container.innerHTML = '<div class="chart-fallback">Why Three endpoint is a placeholder (Backend gap). Decision engine unavailable.</div>';
        return;
    }

    const top3 = UI.getArray(data, 'top3', 'data');
    if (top3.length === 0) {
        container.innerHTML = '<div class="chart-fallback">No resonance match results calculated. The Decision engine requires a minimum number of high-confidence results to rank.</div>';
        return;
    }

    container.innerHTML = top3.map((j, i) => {
        const title = UI.safeField(j.title, 'Untitled Role');
        const company = UI.safeField(j.company, 'Unknown Company');
        const score = UI.safeField(j.resonance_score ?? j.match_score, 0);
        const why = UI.safeField(j.why_included, 'No inclusion telemetry details cataloged (Backend Gap).');

        return `
        <div class="card" style="margin-bottom:var(--space-md); border:1px solid var(--accent);">
            <div style="display:flex; justify-content:space-between;">
                <h4 style="font-weight:700;">Rank #${i+1}: ${title}</h4>
                <span class="badge badge-safe">Match: ${score}%</span>
            </div>
            <p style="font-size:0.9rem; color:var(--muted); margin:4px 0;">Company: ${company}</p>
            <div style="background:rgba(0,0,0,0.2); padding:10px; border-radius:4px; margin-top:8px;">
                <h5 style="font-size:0.8rem; text-transform:uppercase; color:var(--accent);">Evidence Matrix & Selection Logic</h5>
                <p style="font-size:0.8rem; margin-top:4px;">${why}</p>
            </div>
        </div>`;
    }).join('');
}