/* components/filters_facets.js — facet counts, keyword suggest index, provider chips.
   Loaded after filters.js. All helpers are global so filters.js can call them. */

// Parse a job's posting date to epoch ms. Handles ISO/RFC strings, epoch
// numbers, and the relative phrases providers return ("3 days ago", "30+ days
// ago", "today", "yesterday"). Returns NaN when no date is present/parseable —
// so the recency filter and facet counts treat undated jobs identically.
const _REL_UNIT_MS = { minute: 6e4, hour: 36e5, day: 864e5, week: 6048e5, month: 2592e6, year: 31536e6 };
function jobDateMs(job) {
  const v = pick(job, ['published_date', 'posted_at', 'posted_date', 'created', 'created_at', 'date', 'pubDate'], null);
  if (v == null || v === '') return NaN;
  if (typeof v === 'number') return v < 1e12 ? v * 1000 : v;  // epoch s vs ms
  const s = String(v).trim().toLowerCase();
  if (/^(today|just posted|just now|new|active today)/.test(s)) return Date.now();
  if (/^yesterday/.test(s)) return Date.now() - _REL_UNIT_MS.day;
  const rel = s.match(/(\d+)\s*\+?\s*(minute|hour|day|week|month|year)s?\s*ago/);
  if (rel) return Date.now() - Number(rel[1]) * _REL_UNIT_MS[rel[2]];
  const abs = Date.parse(v);
  return isNaN(abs) ? NaN : abs;
}

function _suggestIndex(jobs) {
  const counts = {};
  (jobs || []).forEach(function (j) {
    (Array.isArray(j.tags) ? j.tags : []).forEach(function (tag) {
      const k = String(tag).toLowerCase(); counts[k] = (counts[k] || 0) + 1;
    });
    String(pick(j, ['title','job_title'], '') || '').toLowerCase().split(/[^a-z]+/).forEach(function (w) {
      if (w.length >= 3) counts[w] = (counts[w] || 0) + 1;
    });
  });
  return counts;
}

// Returns counts keyed by dimension value for the entire job set.
// Used to show "(n)" badges next to each filter option.
function facetCounts(jobs) {
  const out = { industry: {}, work_model: {}, job_type: {}, provider: {}, posted_within: {} };
  const _PW = {'24h':864e5,'3d':259.2e6,'7d':604.8e6,'14d':1209.6e6,'30d':2592e6};
  (jobs || []).forEach(function (j) {
    // industry key
    const ik = String(pick(j, ['industry_key'], '') || '').replace(/-/g, '_') ||
                String(pick(j, ['role_family'], '') || '').replace(/-/g, '_');
    if (ik) out.industry[ik] = (out.industry[ik] || 0) + 1;

    // work_model
    const wm = String(pick(j, ['work_model', 'remote_ok', 'job_type_label'], '') || '').toLowerCase();
    if (wm.includes('remote'))  out.work_model.remote  = (out.work_model.remote  || 0) + 1;
    if (wm.includes('on-site') || wm.includes('onsite')) out.work_model.onsite = (out.work_model.onsite || 0) + 1;
    if (wm.includes('hybrid'))  out.work_model.hybrid  = (out.work_model.hybrid  || 0) + 1;

    // job_type
    const jt = JSON.stringify(j).toLowerCase();
    if (jt.includes('full'))     out.job_type.full     = (out.job_type.full     || 0) + 1;
    if (jt.includes('part'))     out.job_type.part     = (out.job_type.part     || 0) + 1;
    if (jt.includes('shift'))    out.job_type.shift    = (out.job_type.shift    || 0) + 1;
    if (jt.includes('contract')) out.job_type.contract = (out.job_type.contract || 0) + 1;

    // provider
    const prov = String(pick(j, ['_provider','source','via','provider'], '') || '').toLowerCase();
    if (prov) out.provider[prov] = (out.provider[prov] || 0) + 1;

    // posted_within — count how many fall within each window
    const d = jobDateMs(j);
    if (!isNaN(d)) {
      const age = Date.now() - d;
      Object.keys(_PW).forEach(function (k) { if (age >= 0 && age <= _PW[k]) out.posted_within[k] = (out.posted_within[k] || 0) + 1; });
    }
  });
  return out;
}

// Provider chip-row rendered inside the filter sheet's Advanced section.
function renderProviderChips(jobs, cur) {
  const counts = {};
  (jobs || []).forEach(function (j) {
    const p = String(pick(j, ['_provider','source','via','provider'], '') || '').toLowerCase();
    if (p) counts[p] = (counts[p] || 0) + 1;
  });
  const provs = Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; }).slice(0, 14);
  if (!provs.length) return '';
  const opts = provs.map(function (p) { return [p, p + ' (' + counts[p] + ')']; });
  return '<div class="filter-block"><span class="filter-block__label">Provider</span>'
    + '<div class="chip-row" data-chipset="provider">'
    + opts.map(function (o) {
        return '<button type="button" class="pill' + (cur === o[0] ? ' is-on' : '') + '" data-val="' + esc(o[0]) + '">' + esc(o[1]) + '</button>';
      }).join('')
    + '</div></div>';
}

// Enhance an already-open filter sheet body with live facet counts.
// Called once when the sheet opens; updates count badges in place.
function applyFacetBadges(body, jobs) {
  const fc = facetCounts(jobs);
  // Update industry <select> option text with counts
  const indSel = body.querySelector('#f-industry');
  if (indSel) {
    Array.from(indSel.options).forEach(function (opt) {
      if (!opt.value) return;
      const n = fc.industry[opt.value];
      if (n != null) opt.text = opt.text.replace(/ \(\d+\)$/, '') + ' (' + n + ')';
    });
  }
  // Update pill buttons that have matching chip-row data
  ['work_model','job_type','posted_within','provider'].forEach(function (dim) {
    const row = body.querySelector('[data-chipset="' + dim + '"]');
    if (!row || !fc[dim]) return;
    row.querySelectorAll('.pill').forEach(function (p) {
      const n = fc[dim][p.dataset.val];
      if (n != null) {
        p.textContent = p.textContent.replace(/ \(\d+\)$/, '') + ' (' + n + ')';
      }
    });
  });
}
