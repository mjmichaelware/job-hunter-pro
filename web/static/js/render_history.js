async function loadHistory() {
    const table = document.getElementById('history-rows');
    table.innerHTML = '<tr><td colspan="5" class="chart-fallback">Querying system batch registry...</td></tr>';
    const data = await safeFetch(API_URLS.history);
    
    if (UI.isPlaceholder(data)) {
        table.innerHTML = '<tr><td colspan="5" class="chart-fallback">History endpoint is currently a placeholder (Backend gap). No batches retrieved.</td></tr>';
        return;
    }

    const batches = UI.getArray(data, 'batches', 'data');
    if (batches.length === 0) {
        table.innerHTML = '<tr><td colspan="5" class="chart-fallback">No batch history exists yet.</td></tr>';
        return;
    }

    table.innerHTML = batches.map(b => {
        // Fallbacks for legacy schema
        const id = UI.safeField(b.batch_id ?? b.object_name, 'Unknown_ID').substring(0, 16);
        const createdRaw = b.created_at ?? b.created_at_utc;
        const created = createdRaw ? new Date(createdRaw).toLocaleString() : 'Unavailable';
        const trigger = UI.safeField(b.trigger, 'Unknown');
        const accepted = b.counts?.accepted ?? (b.accepted ? b.accepted.length : 0);
        const rejected = b.counts?.rejected ?? 0;

        return `
        <tr>
            <td><code>${id}</code></td>
            <td>${created}</td>
            <td><span class="badge badge-cached">${trigger}</span></td>
            <td>${accepted}</td>
            <td>${rejected}</td>
        </tr>`;
    }).join('');
}