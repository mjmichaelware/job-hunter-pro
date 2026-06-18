/* components/sort.js — deterministic client-side sort over loaded jobs.
   Active today on real fields (match, review_score, radius_miles, salary).
   Date options also set AppState.filters.sort so the fetch sends ?sort= for
   when the backend surfaces posted dates (forward-wired). */

const SORT_OPTIONS = [
  { id: 'match_desc', label: 'Match: high → low' },
  { id: 'match_asc', label: 'Match: low → high' },
  { id: 'core_desc', label: 'Core score: high → low' },
  { id: 'core_asc', label: 'Core score: low → high' },
  { id: 'dist_asc', label: 'Distance: near → far' },
  { id: 'dist_desc', label: 'Distance: far → near' },
  { id: 'salary_desc', label: 'Salary: high → low' },
  { id: 'salary_asc', label: 'Salary: low → high' },
  { id: 'date_desc', label: 'Date: newest first' },
  { id: 'date_asc', label: 'Date: oldest first' },
];

function _num(v) { const n = Number(v); return isNaN(n) ? null : n; }
function _salaryNum(job) {
  const s = String(pick(job, ['salary'], '') || '');
  const nums = s.replace(/,/g, '').match(/\d+(\.\d+)?/g);
  if (!nums) return null;
  return Math.max.apply(null, nums.map(Number));
}
function _dateNum(job) {
  const d = pick(job, ['published_date', 'posted_date', 'created', 'date'], null);
  const t = d ? Date.parse(d) : NaN;
  return isNaN(t) ? null : t;
}

// last-resort ordering keeps nulls at the bottom regardless of direction
function _cmp(a, b, dir) {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  return dir === 'asc' ? a - b : b - a;
}

function sortJobs(jobs, mode) {
  const list = (jobs || []).slice();
  const m = mode || AppState.sort || 'match_desc';
  const map = {
    match_desc: [function (j) { return _num(pick(j, ['match', 'match_score'], null)); }, 'desc'],
    match_asc: [function (j) { return _num(pick(j, ['match', 'match_score'], null)); }, 'asc'],
    core_desc: [function (j) { return _num(pick(j, ['review_score'], null)); }, 'desc'],
    core_asc: [function (j) { return _num(pick(j, ['review_score'], null)); }, 'asc'],
    dist_asc: [function (j) { return _num(j.radius_miles); }, 'asc'],
    dist_desc: [function (j) { return _num(j.radius_miles); }, 'desc'],
    salary_desc: [_salaryNum, 'desc'], salary_asc: [_salaryNum, 'asc'],
    date_desc: [_dateNum, 'desc'], date_asc: [_dateNum, 'asc'],
  }[m] || [function (j) { return _num(pick(j, ['match', 'match_score'], null)); }, 'desc'];
  const keyFn = map[0], dir = map[1];
  list.sort(function (a, b) { return _cmp(keyFn(a), keyFn(b), dir); });
  return list;
}

function renderSortControl() {
  const cur = AppState.sort || 'match_desc';
  return '<label class="sort-control">Sort'
    + '<select id="sort-select">' + SORT_OPTIONS.map(function (o) {
        return '<option value="' + o.id + '"' + (o.id === cur ? ' selected' : '') + '>' + esc(o.label) + '</option>';
      }).join('') + '</select></label>';
}
