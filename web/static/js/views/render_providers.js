/* views/render_providers.js — Discovery vs Reasoning provider status.
   LLMs are explicitly labeled reasoning-only — never job discovery. */

function _provStatusCls(s) {
  return s === 'ready' ? 'badge-safe'
    : s === 'disabled_by_policy' ? 'badge-error'
    : 'badge-disabled';
}

function _keyNote(p) {
  if (!p.requires_api_key) return '<span class="badge badge-safe" title="No API key needed">free</span>';
  if (p.is_available) return '<span class="badge badge-safe">key ✓</span>';
  return '<span class="badge badge-disabled">key needed</span>';
}

function _provRow(p) {
  const reason = p.reason ? ' <span class="na">(' + esc(p.reason) + ')</span>' : '';
  return '<tr>'
    + '<td><strong>' + esc(p.label || p.key) + '</strong>'
    + '<div class="provider-key-hint">' + esc(p.key) + '</div></td>'
    + '<td><span class="badge ' + _provStatusCls(p.status) + '">' + esc(p.status || 'unknown') + '</span></td>'
    + '<td>' + _keyNote(p) + '</td>'
    + '<td class="provider-desc">' + esc(p.description || '') + reason + '</td>'
    + '</tr>';
}

function _provTable(list, heading, note) {
  if (!list.length) return '';
  const ready = list.filter(function(p){ return p.status === 'ready'; }).length;
  return '<div class="provider-group">'
    + '<h2 class="section-heading">' + esc(heading)
    + ' <span class="provider-count-chip">' + ready + '/' + list.length + ' ready</span></h2>'
    + (note ? '<p class="section-note">' + esc(note) + '</p>' : '')
    + '<table class="data-table provider-table">'
    + '<thead><tr><th>Provider</th><th>Status</th><th>Key</th><th>Notes</th></tr></thead>'
    + '<tbody>' + list.map(_provRow).join('') + '</tbody>'
    + '</table></div>';
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
  const other     = providers.filter(function (p) { return discovery.indexOf(p) === -1 && reasoning.indexOf(p) === -1; });

  const totalReady = providers.filter(function(p){ return p.status === 'ready'; }).length;
  const totalDorm  = providers.filter(function(p){ return p.status === 'dormant'; }).length;

  const header = sectionHeader({
    icon: 'providers', kicker: 'Source truth',
    title: 'Providers',
    blurb: discovery.length + ' discovery sources · ' + reasoning.length + ' reasoning models registered. '
      + totalReady + ' ready now · ' + totalDorm + ' dormant (need key). '
      + 'Reasoning models classify and score — they never invent job listings.',
  });

  const summary = '<div class="provider-summary-row">'
    + '<span class="badge badge-safe">' + totalReady + ' ready</span>'
    + '<span class="badge badge-disabled">' + totalDorm + ' dormant</span>'
    + '<span class="badge badge-cached">' + providers.length + ' total</span>'
    + '</div>';

  el.innerHTML = header + summary
    + _provTable(discovery, 'Discovery providers', 'These sources retrieve real job listings. Keyless sources are always on; keyed sources activate when you add the key via scripts/add_keys.sh.')
    + _provTable(reasoning, 'Reasoning providers', 'These LLMs classify, enrich, and explain jobs. They are never used for job discovery. Add keys via Google Secret Manager.')
    + (other.length ? _provTable(other, 'Other providers', '') : '');
}

registerView('providers', 'Providers', loadProvidersView);
