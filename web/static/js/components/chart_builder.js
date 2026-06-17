/* components/chart_builder.js — CSS/HTML bar charts from REAL data only.
   No demo arrays. Empty data renders an honest "needs data" state. */

// rows: array of { label, value }. Renders proportional bars.
function cssBars(rows, opts) {
  opts = opts || {};
  const data = (rows || []).filter(function (r) { return r && r.value != null; });
  if (!data.length) {
    return '<p class="state-empty">' + esc(opts.empty || 'Needs more real data to chart.') + '</p>';
  }
  const max = Math.max.apply(null, data.map(function (r) { return Number(r.value) || 0; })) || 1;
  return '<div class="bars">' + data.map(function (r) {
    const pct = Math.max(0, (Number(r.value) || 0) / max * 100);
    return '<div class="bar"><span>' + esc(r.label) + '</span>'
      + '<span class="bar__track"><span class="bar__fill" style="width:' + pct.toFixed(1) + '%"></span></span>'
      + '<span class="bar__val">' + esc(String(r.value)) + '</span></div>';
  }).join('') + '</div>';
}

// Convert a {key: count} object into chart rows.
function countsToRows(obj) {
  return Object.entries(obj || {})
    .map(function (kv) { return { label: kv[0], value: typeof kv[1] === 'object' ? (kv[1].raw_count || kv[1].count || 0) : kv[1] }; })
    .sort(function (a, b) { return b.value - a.value; });
}
