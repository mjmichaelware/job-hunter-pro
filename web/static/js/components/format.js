/* components/format.js — shared display helpers. Honest about missing data:
   null/empty always renders the localized "unavailable", never 0 or a fake value. */

function naSpan() { return ''; }

function formatMins(seconds) {
  if (seconds == null || seconds === '') return '';
  return Math.round(Number(seconds) / 60) + ' min';
}

function formatMiles(miles) {
  if (miles == null || miles === '') return '';
  return Number(miles).toFixed(1) + ' mi';
}

function tagList(items) {
  if (!Array.isArray(items) || !items.length) return '';
  return items.map(function (x) { return '<span class="tag">' + esc(x) + '</span>'; }).join(' ');
}

// Evidence table row: label + value (hidden when missing, never show "unavailable")
function evidenceRow(label, value) {
  if (value === null || value === undefined || value === '') return '';
  return '<tr><th>' + esc(label) + '</th><td>' + esc(String(value)) + '</td></tr>';
}

// Render an honest state block into a node
function renderState(node, cls, msg) {
  if (node) node.innerHTML = '<p class="' + esc(cls) + '">' + esc(msg) + '</p>';
}
