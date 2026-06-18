/* components/filters.js — filter sheet + chips + local apply. Forward-wired:
   controls write to AppState.filters; api.js buildQuery() sends every key as a
   query param (origin, posted_within, min_role_fit, suggest…) so they activate
   automatically once the backend honors them. Local apply uses real fields now. */

const DATE_WINDOWS = [['24h', 'Last 24h'], ['3d', 'Last 3d'], ['5d', 'Last 5d'], ['7d', 'Last 7d'], ['10d', 'Last 10d'], ['14d', 'Last 2wk'], ['30d', 'Last 30d']];
const QUICK_APPLY_RE = /indeed|snagajob|ziprecruiter|easyapply|easy-apply/i;

function filterCountBadge(f) {
  const n = Object.keys(f || {}).filter(function (k) { return k !== 'sort' && f[k] !== '' && f[k] != null; }).length;
  return n ? ' <span class="badge badge-cached">' + n + '</span>' : '';
}

function renderChips(filters) {
  const f = filters || {};
  const keys = Object.keys(f).filter(function (k) { return k !== 'sort' && f[k] !== '' && f[k] != null; });
  if (!keys.length) return '';
  return '<div class="chip-strip">' + keys.map(function (k) {
    return '<span class="chip">' + esc(k) + ': ' + esc(String(f[k]))
      + '<button type="button" class="chip__x" data-chip="' + esc(k) + '" aria-label="Remove ' + esc(k) + '">×</button></span>';
  }).join('') + '</div>';
}

function _chips(name, opts, cur) {
  return '<div class="chip-row" data-chipset="' + name + '">' + opts.map(function (o) {
    const val = o[0], lab = o[1];
    return '<button type="button" class="pill' + (cur === val ? ' is-on' : '') + '" data-val="' + esc(val) + '">' + esc(lab) + '</button>';
  }).join('') + '</div>';
}

function renderFilters(filters, industries) {
  const f = filters || {};
  const ind = (industries || []).map(function (i) { return '<option value="' + esc(i.key) + '"' + (f.industry === i.key ? ' selected' : '') + '>' + esc(i.label) + '</option>'; }).join('');
  return '<div class="filter-form">'
    + '<label>Industry<select id="f-industry"><option value="">All</option>' + ind + '</select></label>'
    + '<label>Role / keyword<input type="text" id="f-q" autocomplete="off" value="' + esc(f.q || '') + '" placeholder="cook, server, front desk…"><div id="f-suggest" class="suggest"></div></label>'
    + '<label>Start location (address / zip / city)<input type="text" id="f-origin" value="' + esc(f.origin || '') + '" placeholder="28 E Bryan Ave, 84115"></label>'
    + '<div class="filter-block"><span class="filter-block__label">Posted within</span>' + _chips('posted_within', DATE_WINDOWS, f.posted_within) + '</div>'
    + '<label>Min Core Rating <span class="na">(Google today; +Glassdoor/BBB coming)</span><input type="range" id="f-core" min="0" max="100" value="' + esc(f.min_core || 0) + '"></label>'
    + '<label>Min role fit<input type="range" id="f-rolefit" min="0" max="100" value="' + esc(f.min_role_fit || 0) + '"></label>'
    + '<label>Max transit (min)<input type="number" id="f-transit" min="0" max="120" value="' + esc(f.max_transit || '') + '" placeholder="any"></label>'
    + '<label>Max radius (mi)<input type="number" id="f-radius" min="0" max="50" step="0.5" value="' + esc(f.max_radius || '') + '" placeholder="any"></label>'
    + '<div class="filter-block"><span class="filter-block__label">Work model</span>' + _chips('work_model', [['remote', 'Remote'], ['onsite', 'On-site'], ['hybrid', 'Hybrid']], f.work_model) + '</div>'
    + '<div class="filter-block"><span class="filter-block__label">Type</span>' + _chips('job_type', [['full', 'Full-time'], ['part', 'Part-time'], ['shift', 'Shift'], ['contract', 'Contract']], f.job_type) + '</div>'
    + '<label class="check"><input type="checkbox" id="f-quick"' + (f.quick_apply ? ' checked' : '') + '> Quick-apply channels only</label>'
    + '<div class="filter-actions"><button type="button" id="f-apply" class="btn">Apply</button><button type="button" id="f-clear" class="btn">Clear</button></div>'
    + '</div>';
}

function readFilters(c) {
  const f = {};
  const g = function (id) { const el = c.querySelector(id); return el ? el.value : ''; };
  if (g('#f-industry')) f.industry = g('#f-industry');
  if (g('#f-q')) f.q = g('#f-q');
  if (g('#f-origin')) f.origin = g('#f-origin');
  if (Number(g('#f-core')) > 0) f.min_core = g('#f-core');
  if (Number(g('#f-rolefit')) > 0) f.min_role_fit = g('#f-rolefit');
  if (g('#f-transit')) f.max_transit = g('#f-transit');
  if (g('#f-radius')) f.max_radius = g('#f-radius');
  const chk = c.querySelector('#f-quick'); if (chk && chk.checked) f.quick_apply = '1';
  ['posted_within', 'work_model', 'job_type'].forEach(function (name) {
    const on = c.querySelector('[data-chipset="' + name + '"] .pill.is-on');
    if (on) f[name] = on.dataset.val;
  });
  if (AppState.sort) f.sort = AppState.sort;
  return f;
}

function applyLocalFilters(jobs, f) {
  if (!f) return jobs;
  const txt = function (j) { return JSON.stringify(j).toLowerCase(); };
  return jobs.filter(function (j) {
    if (f.industry && pick(j, ['industry', 'role_family'], '') !== f.industry) return false;
    if (f.min_core != null && j.review_score != null && Number(j.review_score) < Number(f.min_core)) return false;
    if (f.min_role_fit != null && pick(j, ['match', 'match_score'], null) != null && Number(pick(j, ['match', 'match_score'], 0)) < Number(f.min_role_fit)) return false;
    if (f.max_transit && j.commute_seconds != null && j.commute_seconds / 60 > Number(f.max_transit)) return false;
    if (f.max_radius && j.radius_miles != null && Number(j.radius_miles) > Number(f.max_radius)) return false;
    if (f.quick_apply && !QUICK_APPLY_RE.test(String(pick(j, ['source_url', 'url', '_provider', 'via'], '')))) return false;
    if (f.work_model && txt(j).indexOf(f.work_model === 'onsite' ? 'on-site' : f.work_model) === -1) return false;
    if (f.job_type) { const map = { full: 'full', part: 'part', shift: 'shift', contract: 'contract' }; if (txt(j).indexOf(map[f.job_type]) === -1) return false; }
    if (f.q && txt(j).indexOf(String(f.q).toLowerCase()) === -1) return false;
    return true;
  });
}

// suggestion index from the loaded set (title words + tags) with real counts
function _suggestIndex(jobs) {
  const counts = {};
  (jobs || []).forEach(function (j) {
    (Array.isArray(j.tags) ? j.tags : []).forEach(function (tag) { const k = String(tag).toLowerCase(); counts[k] = (counts[k] || 0) + 1; });
    String(pick(j, ['title', 'job_title'], '') || '').toLowerCase().split(/[^a-z]+/).forEach(function (w) { if (w.length >= 3) counts[w] = (counts[w] || 0) + 1; });
  });
  return counts;
}

function openFiltersSheet(industries, jobs, onApply) {
  openSheet(t('filters.title'), renderFilters(AppState.filters, industries), function (body) {
    body.querySelectorAll('.chip-row').forEach(function (row) {
      row.querySelectorAll('.pill').forEach(function (p) {
        p.addEventListener('click', function () {
          const was = p.classList.contains('is-on');
          row.querySelectorAll('.pill').forEach(function (x) { x.classList.remove('is-on'); });
          if (!was) p.classList.add('is-on');
        });
      });
    });
    const q = body.querySelector('#f-q'); const sug = body.querySelector('#f-suggest');
    const idx = _suggestIndex(jobs);
    if (q && sug) q.addEventListener('input', function () {
      const v = q.value.toLowerCase().trim();
      if (!v) { sug.innerHTML = ''; return; }
      const hits = Object.keys(idx).filter(function (k) { return k.indexOf(v) !== -1; }).sort(function (a, b) { return idx[b] - idx[a]; }).slice(0, 8);
      sug.innerHTML = hits.map(function (k) { return '<button type="button" class="suggest__item" data-q="' + esc(k) + '">' + esc(k) + ' <span class="na">[' + idx[k] + ']</span></button>'; }).join('');
      sug.querySelectorAll('.suggest__item').forEach(function (b) { b.addEventListener('click', function () { q.value = b.dataset.q; sug.innerHTML = ''; }); });
    });
    body.querySelector('#f-apply').addEventListener('click', function () { AppState.filters = readFilters(body); closeSheet(); if (onApply) onApply(); });
    body.querySelector('#f-clear').addEventListener('click', function () { AppState.filters = AppState.sort ? { sort: AppState.sort } : {}; closeSheet(); if (onApply) onApply(); });
  });
}
