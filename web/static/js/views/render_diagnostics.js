/* views/render_diagnostics.js — system diagnostics: health, provider summary,
   and AI key-wiring status. Safe: /api/health + /api/providers only. */

function _flagRow(label, on) {
  const cls = on ? 'badge-safe' : 'badge-disabled';
  return '<tr><th>' + esc(label) + '</th><td><span class="badge ' + cls + '">'
    + (on ? '✓ enabled' : '✗ off') + '</span></td></tr>';
}

function _providerSummary(providers, hProviders) {
  if (!Array.isArray(providers) || !providers.length) {
    const hp = hProviders || {};
    return '<div class="info-box">Provider list unavailable from /api/providers.'
      + (hp.total != null ? ' Health reports ' + hp.total + ' total, ' + (hp.ready || 0) + ' ready.' : '')
      + '</div>';
  }
  const ready = providers.filter(function (p) { return p.status === 'ready'; }).length;
  const dormant = providers.filter(function (p) { return p.status === 'dormant'; }).length;
  const search = providers.filter(function (p) { return p.type === 'search'; }).length;
  const reasoning = providers.filter(function (p) { return p.type === 'reasoning'; }).length;
  return '<div class="card-row">'
    + '<div class="stat-card"><div class="stat-card__label">Total</div><div class="stat-card__value">' + providers.length + '</div></div>'
    + '<div class="stat-card"><div class="stat-card__label">Ready</div><div class="stat-card__value"><span class="badge badge-safe">' + ready + '</span></div></div>'
    + '<div class="stat-card"><div class="stat-card__label">Dormant</div><div class="stat-card__value"><span class="badge badge-disabled">' + dormant + '</span></div></div>'
    + '<div class="stat-card"><div class="stat-card__label">Discovery</div><div class="stat-card__value">' + search + '</div></div>'
    + '<div class="stat-card"><div class="stat-card__label">Reasoning</div><div class="stat-card__value">' + reasoning + '</div></div>'
    + '</div>';
}

async function loadDiagnosticsView() {
  const el = mount(); if (!el) return;
  const [h, provData] = await Promise.all([safeFetch('/api/health'), safeFetch('/api/providers')]);
  if (!h) { renderState(el, 'state-error', 'Backend unreachable — /api/health did not respond.'); return; }

  const ok = (h.status === 'ok' || h.status === 'healthy');
  const providers = arr(provData, ['providers']);

  let html = sectionHeader({
    icon: 'system', kicker: 'Diagnostics',
    title: 'System health',
    blurb: 'Live backend status, version, provider summary, and AI key-wiring. Read-only — this view never spends quota.',
  }) + '<section class="diagnostics">'
    + '<div class="card-row">'
    + '<div class="stat-card"><div class="stat-card__label">Status</div><div class="stat-card__value">'
    + '<span class="badge ' + (ok ? 'badge-safe' : 'badge-error') + '">' + esc(h.status || 'unknown') + '</span></div></div>'
    + '<div class="stat-card"><div class="stat-card__label">Version</div><div class="stat-card__value" style="font-size:0.95rem">' + esc(h.version || 'unknown') + '</div></div>'
    + '<div class="stat-card"><div class="stat-card__label">Runtime</div><div class="stat-card__value" style="font-size:0.95rem">' + esc(h.runtime || 'unavailable') + '</div></div>'
    + '<div class="stat-card"><div class="stat-card__label">Origin geocoded</div><div class="stat-card__value">' + (h.origin_geocoded ? '✓' : '—') + '</div></div>'
    + '</div>';

  html += '<h2 class="section-heading">Providers</h2>'
    + _providerSummary(providers, h.providers);

  html += '<h2 class="section-heading">AI key-wiring</h2><table class="data-table"><tbody>'
    + _flagRow('Google Maps', h.maps_enabled)
    + _flagRow('SerpAPI', h.serpapi_enabled)
    + _flagRow('OpenAI', h.openai_enabled)
    + _flagRow('Gemini', h.gemini_enabled)
    + _flagRow('Claude', h.claude_enabled)
    + _flagRow('Groq', h.groq_enabled)
    + _flagRow('xAI / Grok', h.grok_xai_enabled)
    + '</tbody></table>';

  html += '<h2 class="section-heading">Origin & limits</h2><table class="data-table"><tbody>'
    + '<tr><th>Origin</th><td>' + esc(h.origin || 'unavailable') + '</td></tr>'
    + '<tr><th>Max radius</th><td>' + (h.max_radius_miles != null ? esc(String(h.max_radius_miles)) + ' mi' : 'unavailable') + '</td></tr>'
    + '<tr><th>Max transit</th><td>' + (h.max_transit_minutes != null ? esc(String(h.max_transit_minutes)) + ' min (filter only)' : 'no cap') + '</td></tr>'
    + '<tr><th>Batch bucket</th><td>' + esc(h.batch_bucket || 'unavailable') + '</td></tr>'
    + '</tbody></table>';

  if (Array.isArray(h.pipeline) && h.pipeline.length) {
    html += '<h2 class="section-heading">Pipeline stages</h2><div class="bento__flags">' + tagList(h.pipeline) + '</div>';
  }
  html += '</section>';
  el.innerHTML = html;
}

registerView('diagnostics', 'System', loadDiagnosticsView);
