async function loadHistory(){const table=document.getElementById('history-rows');table.innerHTML='<tr><td colspan="5" class="chart-fallback">Querying system batch registry...</td></tr>';const data=await safeFetch(API_URLS.history);if(!data||!data.batches||data.batches.length===0){table.innerHTML='<tr><td colspan="5" class="chart-fallback">No batch history exists yet.</td></tr>';return}table.innerHTML=data.batches.map(b=>`
<tr>
    <td><code>${b.batch_id.substring(0,8)}</code></td>
    <td>${new Date(b.created_at).toLocaleString()}</td>
    <td><span class="badge badge-cached">${b.trigger}</span></td>
    <td>${b.counts?.accepted || 0}</td>
    <td>${b.counts?.rejected || 0}</td>
</tr>`).join('')}