/* views/render_diagnostics.js — system diagnostics (the version string + provider
   flags that used to clutter the header live here). Safe: /api/health only. */

function _flagRow(label, on) {
  const cls = on ? 'badge-safe' : 'badge-disabled';
  return '<tr><th>' + esc(label) + '</th><td><span class="badge ' + cls + '">' + (on ? 'enabled' : 'off') + '</span></td></tr>';
}

async function loadDiagnosticsView() {
  const el = mount(); if (!el) return;
  const h = await safeFetch('/api/health');
  if (!h) { renderState(el, 'state-error', 'Backend unreachable — /api/health did not respond.'); return; }

  const ok = (h.status === 'ok' || h.status === 'healthy');
  let html = '<section class="diagnostics">'
    + '<div class="card-row">'
    + '<div class="stat-card"><div class="stat-card__label">Status</div><div class="stat-card__value">'
    + '<span class="badge ' + (ok ? 'badge-safe' : 'badge-error') + '">' + esc(h.status || 'unknown') + '</span></div></div>'
    + '<div class="stat-card"><div class="stat-card__label">Version</div><div class="stat-card__value" style="font-size:0.95rem">' + esc(h.version || 'unknown') + '</div></div>'
    + '<div class="stat-card"><div class="stat-card__label">Runtime</div><div class="stat-card__value" style="font-size:0.95rem">' + esc(h.runtime || 'unavailable') + '</div></div>'
    + '<div class="stat-card"><div class="stat-card__label">Origin geocoded</div><div class="stat-card__value">' + (h.origin_geocoded ? '✓' : '—') + '</div></div>'
    + '</div>';

  html += '<h2 class="section-heading">Providers</h2><table class="data-table"><tbody>'
    + _flagRow('SerpAPI', h.serpapi_enabled)
    + _flagRow('Google Maps', h.maps_enabled)
    + _flagRow('Groq', h.groq_enabled)
    + _flagRow('OpenAI', h.openai_enabled)
    + _flagRow('Gemini', h.gemini_enabled)
    + _flagRow('Claude', h.claude_enabled)
    + _flagRow('xAI / Grok', h.grok_xai_enabled)
    + '</tbody></table>';

  html += '<h2 class="section-heading">Origin & limits</h2><table class="data-table"><tbody>'
    + '<tr><th>Origin</th><td>' + esc(h.origin || 'unavailable') + '</td></tr>'
    + '<tr><th>Max radius</th><td>' + (h.max_radius_miles != null ? esc(String(h.max_radius_miles)) + ' mi' : 'unavailable') + '</td></tr>'
    + '<tr><th>Max transit</th><td>' + (h.max_transit_minutes != null ? esc(String(h.max_transit_minutes)) + ' min' : 'unavailable') + '</td></tr>'
    + '<tr><th>Budget mode</th><td>' + (h.serpapi_budget_mode ? 'on' : 'off') + '</td></tr>'
    + '<tr><th>Min searches guard</th><td>' + esc(String(h.serpapi_min_searches_left != null ? h.serpapi_min_searches_left : 'unavailable')) + '</td></tr>'
    + '<tr><th>Batch bucket</th><td>' + esc(h.batch_bucket || 'unavailable') + '</td></tr>'
    + '</tbody></table>';

  if (Array.isArray(h.pipeline) && h.pipeline.length) {
    html += '<h2 class="section-heading">Pipeline stages</h2><div class="bento__flags">' + tagList(h.pipeline) + '</div>';
  }
  html += '</section>';
  el.innerHTML = html;
}

registerView('diagnostics', 'System', loadDiagnosticsView);
