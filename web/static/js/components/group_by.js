/* components/group_by.js — bucket jobs into labeled sections.
   Uses fields already on jobs: role_family (industry-ish) and title/role. */

const GROUP_OPTIONS = [
  { id: 'none', label: 'No grouping' },
  { id: 'industry', label: 'By industry / role family' },
  { id: 'role', label: 'By job / role' },
];

function _roleKey(job) {
  const t = String(pick(job, ['title', 'job_title'], '') || '').toLowerCase();
  // collapse to a coarse role token from the title's leading words
  const tags = Array.isArray(job.tags) ? job.tags : [];
  if (tags.length) return tags[0];
  return t.split(/[,\-–|(]/)[0].trim() || 'other';
}

// returns ordered array of { label, jobs }
function groupJobs(jobs, mode) {
  const m = mode || AppState.groupBy || 'none';
  if (m === 'none' || !jobs.length) return [{ label: '', jobs: jobs }];
  const keyFn = m === 'industry'
    ? function (j) { return pick(j, ['role_family', 'industry'], 'uncategorized'); }
    : _roleKey;
  const buckets = {};
  jobs.forEach(function (j) {
    const k = String(keyFn(j) || 'uncategorized');
    (buckets[k] = buckets[k] || []).push(j);
  });
  return Object.keys(buckets).sort(function (a, b) { return buckets[b].length - buckets[a].length; })
    .map(function (k) { return { label: k + ' (' + buckets[k].length + ')', jobs: buckets[k] }; });
}

function renderGroupControl() {
  const cur = AppState.groupBy || 'none';
  return '<label class="group-control">Group'
    + '<select id="group-select">' + GROUP_OPTIONS.map(function (o) {
        return '<option value="' + o.id + '"' + (o.id === cur ? ' selected' : '') + '>' + esc(o.label) + '</option>';
      }).join('') + '</select></label>';
}
