/* views/render_applications.js — Apply tracker with job/company context.
   Loads application records + cross-references batch data to show job details. */

const APP_STATUSES = ['DISCOVERED', 'APPLIED', 'INTERVIEWING', 'OFFERED', 'REJECTED', 'WITHDRAWN'];

function _appStatusCls(s) {
  return s === 'OFFERED' ? 'badge-safe' : s === 'REJECTED' ? 'badge-error'
    : s === 'INTERVIEWING' ? 'badge-warn' : 'badge-cached';
}

function _initials(name) {
  return (name || '?').split(' ').slice(0, 2).map(function (w) { return w[0] || ''; }).join('').toUpperCase() || '?';
}

async function _buildJobIndex() {
  // Build a job_id → job lookup from the IndexedDB cache or recent batch
  const cached = JHP_SYNC && JHP_SYNC.recall ? JHP_SYNC.recall('jobs') : null;
  if (cached && Array.isArray(cached)) {
    const idx = {};
    cached.forEach(function (j) { if (j.job_id) idx[j.job_id] = j; });
    return idx;
  }
  try {
    const batchList = await safeFetch('/api/batches');
    const batches = arr(batchList, ['batches']).slice(0, 2);
    const idx = {};
    for (const b of batches) {
      const snap = await safeFetch('/api/batches/' + encodeURIComponent(b.id || b));
      arr(snap, ['data', 'jobs', 'accepted', 'results']).forEach(function (j) { if (j.job_id) idx[j.job_id] = j; });
    }
    return idx;
  } catch (e) { return {}; }
}

async function loadApplicationsView() {
  const el = mount(); if (!el) return;
  el.innerHTML = '<p class="state-loading">Loading your application pipeline…</p>';

  const [data, jobIndex] = await Promise.all([
    safeFetch('/api/applications'),
    _buildJobIndex(),
  ]);

  if (!data) { renderState(el, 'state-error', 'Could not load applications.'); return; }
  JHP_SYNC.remember('applications', data);
  const apps = arr(data, ['applications']);

  let html = '<div class="apps-header">'
    + '<h2 class="section-heading">Your Application Pipeline</h2>'
    + '<p class="status-line">Track every opportunity — stay organized and follow up with confidence.</p>'
    + '</div>';

  if (!apps.length) {
    html += '<div class="info-box">No tracked applications yet. Open any job card and press <strong>"Track this job"</strong> to start tracking.</div>';
    el.innerHTML = html; return;
  }

  html += '<div class="apps-list">'
    + apps.map(function (a) {
        const jid = a.job_id || '';
        const job = jobIndex[jid] || {};
        const title = esc(job.title || '');
        const co = esc(cleanText(job.company || job.company_name || '', ''));
        const url = href(job.url || job.source_url || '');
        const initials = _initials(co || title || jid.slice(0, 4).toUpperCase());
        const opts = APP_STATUSES.map(function (s) {
          return '<option value="' + s + '"' + (s === a.status ? ' selected' : '') + '>' + s + '</option>';
        }).join('');

        return '<div class="app-card bento">'
          + '<div class="app-card__avatar" aria-hidden="true">' + esc(initials) + '</div>'
          + '<div class="app-card__body">'
          + '<div class="app-card__title">' + (title || '<span class="na">' + esc(jid.slice(0, 16)) + '…</span>') + '</div>'
          + (co ? '<div class="app-card__co">' + co + '</div>' : '')
          + '<div class="app-card__meta">'
          + '<span class="badge ' + _appStatusCls(a.status) + '">' + esc(a.status || 'unknown') + '</span>'
          + (a.created_at ? ' <span class="tag">Applied ' + esc(a.created_at.slice(0, 10)) + '</span>' : '')
          + (a.notes ? ' <span class="tag">' + esc(a.notes.slice(0, 40)) + '</span>' : '')
          + '</div>'
          + '<div class="app-card__actions">'
          + (url ? '<a class="btn-link" href="' + url + '" target="_blank" rel="noopener noreferrer">Open job ↗</a> ' : '')
          + '<select class="status-select" data-job-id="' + esc(jid) + '">' + opts + '</select> '
          + '<button type="button" class="btn-sm btn-save-status" data-job-id="' + esc(jid) + '">Save</button>'
          + '</div></div></div>';
      }).join('')
    + '</div>';

  el.innerHTML = html;

  el.querySelectorAll('.btn-save-status').forEach(function (btn) {
    btn.addEventListener('click', async function () {
      const jid = btn.dataset.jobId;
      const sel = el.querySelector('.status-select[data-job-id="' + jid.replace(/"/g, '\\"') + '"]');
      if (!sel) return;
      btn.disabled = true; btn.textContent = 'Saving…';
      try {
        const res = await fetch('/api/applications/' + encodeURIComponent(jid), {
          method: 'PATCH', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: sel.value }),
        });
        btn.textContent = res.ok ? 'Saved ✓' : 'Failed';
        if (res.ok) window.setTimeout(function () { btn.textContent = 'Save'; btn.disabled = false; }, 1500);
        else btn.disabled = false;
      } catch (e) { btn.textContent = 'Error'; btn.disabled = false; }
    });
  });
}

registerView('applications', 'Applications', loadApplicationsView);
