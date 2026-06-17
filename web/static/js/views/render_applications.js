/* views/render_applications.js — manual apply tracker (GET list, PATCH status). */

const APP_STATUSES = ['DISCOVERED', 'APPLIED', 'INTERVIEWING', 'OFFERED', 'REJECTED', 'WITHDRAWN'];

function _appStatusCls(s) {
  return s === 'OFFERED' ? 'badge-safe' : s === 'REJECTED' ? 'badge-error' : s === 'INTERVIEWING' ? 'badge-warn' : 'badge-cached';
}

async function loadApplicationsView() {
  const data = await safeFetch('/api/applications');
  const el = mount(); if (!el) return;
  if (!data) { renderState(el, 'state-error', 'Could not load applications.'); return; }
  JHP_SYNC.remember('applications', data);
  const apps = arr(data, ['applications']);

  if (!apps.length) {
    renderState(el, 'state-empty', 'No tracked applications yet. Open a job card and press "Track this job" to start tracking.');
    return;
  }

  let html = '<table class="data-table"><thead><tr><th>Job ID</th><th>Status</th><th>Notes</th><th>Created</th><th>Updated</th><th>Change</th></tr></thead><tbody>';
  apps.forEach(function (a) {
    const jid = esc(a.job_id || '');
    const opts = APP_STATUSES.map(function (s) { return '<option value="' + s + '"' + (s === a.status ? ' selected' : '') + '>' + s + '</option>'; }).join('');
    html += '<tr><td><code>' + jid + '</code></td>'
      + '<td><span class="badge ' + _appStatusCls(a.status) + '">' + esc(a.status || 'unknown') + '</span></td>'
      + '<td>' + esc(a.notes || '') + '</td>'
      + '<td>' + esc(a.created_at || '—') + '</td>'
      + '<td>' + esc(a.updated_at || '—') + '</td>'
      + '<td><select class="status-select" data-job-id="' + jid + '">' + opts + '</select> '
      + '<button type="button" class="btn-sm btn-save-status" data-job-id="' + jid + '">Save</button></td></tr>';
  });
  html += '</tbody></table>';
  el.innerHTML = html;

  el.querySelectorAll('.btn-save-status').forEach(function (btn) {
    btn.addEventListener('click', async function () {
      const jid = btn.dataset.jobId;
      const sel = el.querySelector('.status-select[data-job-id="' + jid.replace(/"/g, '\\"') + '"]');
      if (!sel) return;
      btn.disabled = true; btn.textContent = 'Saving…';
      try {
        const res = await fetch('/api/applications/' + encodeURIComponent(jid), {
          method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: sel.value }),
        });
        btn.textContent = res.ok ? 'Saved' : 'Failed';
        if (res.ok) window.setTimeout(function () { btn.textContent = 'Save'; btn.disabled = false; }, 1500);
        else btn.disabled = false;
      } catch (e) { btn.textContent = 'Error'; btn.disabled = false; }
    });
  });
}

registerView('applications', 'Applications', loadApplicationsView);
