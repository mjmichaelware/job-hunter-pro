/* components/format.js — shared display helpers. Honest about missing data:
   null/empty always renders the localized "unavailable", never 0 or a fake value. */

function naSpan() { return '<span class="na">' + esc(t('common.unavailable')) + '</span>'; }

function formatMins(seconds) {
  if (seconds == null || seconds === '') return t('common.unavailable');
  return Math.round(Number(seconds) / 60) + ' min';
}

function formatMiles(miles) {
  if (miles == null || miles === '') return t('common.unavailable');
  return Number(miles).toFixed(1) + ' mi';
}

function tagList(items) {
  if (!Array.isArray(items) || !items.length) return '';
  return items.map(function (x) { return '<span class="tag">' + esc(x) + '</span>'; }).join(' ');
}

// Evidence table row: label + value (or honest "unavailable")
function evidenceRow(label, value) {
  const display = (value === null || value === undefined || value === '') ? naSpan() : esc(String(value));
  return '<tr><th>' + esc(label) + '</th><td>' + display + '</td></tr>';
}

// Render an honest state block into a node
function renderState(node, cls, msg) {
  if (node) node.innerHTML = '<p class="' + esc(cls) + '">' + esc(msg) + '</p>';
}
