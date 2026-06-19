/* views/render_budget.js — Discovery engine health: providers, storage, API stats.
   SerpAPI quota removed. Shows what's live and what to unlock next. */

function _providerHealthCard(p) {
  const key = p.key || p.id || '';
  const label = p.label || key;
  const avail = p.available || p.status === 'available';
  const dormant = !avail && !p.disabled_reason;
  const cls = avail ? 'badge-safe' : dormant ? 'badge-warn' : 'badge-disabled';
  const statusText = avail ? 'live' : dormant ? 'needs key' : 'off';
  return '<div class="stat-card stat-card--provider">'
    + '<div class="stat-card__label">' + esc(label) + '</div>'
    + '<div class="stat-card__value"><span class="badge ' + cls + '">' + statusText + '</span></div>'
    + (p.disabled_reason ? '<div class="stat-card__sub" style="font-size:0.7rem;color:var(--c-muted)">' + esc(p.disabled_reason.slice(0, 60)) + '</div>' : '')
    + '</div>';
}

async function loadBudgetView() {
  const el = mount(); if (!el) return;
  el.innerHTML = '<p class="state-loading">Loading engine status…</p>';

  const [provData, usageData, healthData] = await Promise.all([
    safeFetch('/api/providers'),
    safeFetch('/api/usage'),
    safeFetch('/api/health'),
  ]);

  const providers = provData ? (provData.providers || []) : [];
  const pList = Array.isArray(providers) ? providers : Object.values(providers);
  const liveProviders = pList.filter(function (p) { return p.available || p.status === 'available'; });
  const dormantProviders = pList.filter(function (p) { return !p.available && !p.disabled_reason; });
  const offProviders = pList.filter(function (p) { return !p.available && p.disabled_reason; });

  const storage = (usageData && usageData.storage) || {};
  const ok = healthData && (healthData.status === 'ok' || healthData.status === 'healthy');
  const ver = healthData && healthData.version ? healthData.version : null;

  let html = sectionHeader({
    icon: 'budget', kicker: 'Engine status',
    title: 'Discovery economy',
    blurb: 'Powered by ' + pList.length + '+ free-tier providers with no quota limits. See what is live, what unlocks with a key, and how storage and system health look right now.',
  });

  // Live count stats
  html += '<div class="card-row">'
    + '<div class="stat-card"><div class="stat-card__label">Active providers</div>'
    + '<div class="stat-card__value">' + liveProviders.length + '</div></div>'
    + '<div class="stat-card"><div class="stat-card__label">Needs key</div>'
    + '<div class="stat-card__value">' + dormantProviders.length + '</div></div>'
    + '<div class="stat-card"><div class="stat-card__label">Default-off</div>'
    + '<div class="stat-card__value">' + offProviders.length + '</div></div>'
    + '<div class="stat-card"><div class="stat-card__label">System</div>'
    + '<div class="stat-card__value"><span class="badge ' + (ok ? 'badge-safe' : 'badge-error') + '">'
    + (ok ? 'ok' : 'unreachable') + '</span></div></div>'
    + '</div>';

  // Provider health grid
  if (liveProviders.length) {
    html += '<h2 class="section-heading">🟢 Live providers</h2>'
      + '<div class="card-row card-row--wrap">' + liveProviders.map(_providerHealthCard).join('') + '</div>';
  }
  if (dormantProviders.length) {
    html += '<h2 class="section-heading">🔑 Unlock with a key</h2>'
      + '<div class="card-row card-row--wrap">' + dormantProviders.map(_providerHealthCard).join('') + '</div>';
  }
  if (offProviders.length) {
    html += '<h2 class="section-heading">⛔ Default-off (opt in with env flag)</h2>'
      + '<div class="card-row card-row--wrap">' + offProviders.map(_providerHealthCard).join('') + '</div>';
  }

  // Storage
  if (Object.keys(storage).length) {
    html += '<h2 class="section-heading">Storage</h2>'
      + '<table class="data-table"><tbody>'
      + Object.entries(storage).map(function (kv) {
          return '<tr><th>' + esc(kv[0]) + '</th><td>' + esc(String(kv[1])) + '</td></tr>';
        }).join('')
      + '</tbody></table>';
  }

  // System health footer
  if (ver) {
    html += '<div class="info-box"><strong>Version:</strong> ' + esc(ver)
      + ' &nbsp;·&nbsp; <strong>Status:</strong> ' + (ok ? '✓ healthy' : '✗ unreachable') + '</div>';
  }

  html += '<div class="info-box"><strong>Free to use:</strong> Opening this dashboard costs nothing. '
    + 'Discovery runs query live provider APIs. All ' + liveProviders.length + ' active providers are free-tier.</div>';

  el.innerHTML = html;
  JHP_SYNC.remember('budget', { providers: pList, liveCount: liveProviders.length });
}

registerView('budget', 'Budget', loadBudgetView);
