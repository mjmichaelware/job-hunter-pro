/* views/render_providers.js — Discovery vs Reasoning provider status.
   LLMs are explicitly labeled reasoning-only — never job discovery. */

function _provStatusCls(s) {
  return s === 'ready' ? 'badge-safe'
    : s === 'disabled_by_policy' ? 'badge-error'
    : 'badge-disabled';
}

function _provRow(p) {
  const keyNote = p.requires_api_key ? (p.is_available ? '' : ' — key missing') : ' — no key needed';
  const reason = p.reason ? '<span class="na"> (' + esc(p.reason) + ')</span>' : '';
  return '<tr><td>' + esc(p.label || p.key) + '</td>'
    + '<td><span class="badge ' + _provStatusCls(p.status) + '">' + esc(p.status || 'unknown') + '</span></td>'
    + '<td>' + esc(p.description || '') + keyNote + reason + '</td></tr>';
}

function _provTable(list, heading, note) {
  if (!list.length) return '';
  return '<h2 class="section-heading">' + esc(heading) + '</h2>'
    + (note ? '<p class="section-note">' + esc(note) + '</p>' : '')
    + '<table class="data-table"><thead><tr><th>Provider</th><th>Status</th><th>Notes</th></tr></thead><tbody>'
    + list.map(_provRow).join('') + '</tbody></table>';
}

async function loadProvidersView() {
  const data = await safeFetch('/api/providers');
  const el = mount(); if (!el) return;
  if (!data) { renderState(el, 'state-error', 'Could not load providers.'); return; }
  JHP_SYNC.remember('providers', data);
  const providers = arr(data, ['providers']);
  if (!providers.length) { renderState(el, 'state-empty', 'No providers registered.'); return; }

  const discovery = providers.filter(function (p) { return p.type === 'discovery' || p.type === 'search'; });
  const reasoning = providers.filter(function (p) { return p.type === 'reasoning' || p.type === 'llm'; });
  const other = providers.filter(function (p) { return discovery.indexOf(p) === -1 && reasoning.indexOf(p) === -1; });

  el.innerHTML = _provTable(discovery, 'Discovery providers', 'These providers retrieve real job listings.')
    + _provTable(reasoning, 'Reasoning providers', 'Reasoning only — these LLMs classify, extract, and score. They are never used for job discovery.')
    + _provTable(other, 'Other providers', '');
}

registerView('providers', 'Providers', loadProvidersView);
