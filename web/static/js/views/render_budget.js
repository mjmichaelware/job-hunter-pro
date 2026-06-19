/* views/render_budget.js — Discovery engine health: providers, storage, API stats.
   SerpAPI quota removed. Shows what's live and what to unlock next. */

/* /api/providers contract (api/providers.py): is_available, status
   ('ready'|'dormant'|'disabled_by_policy'), reason, disabled_by_policy,
   requires_api_key. Read those exact fields — older code read available/
   disabled_reason which are absent, so every keyed provider wrongly showed
   "needs key". */
function provLive(p)    { return p.is_available === true || p.status === 'ready'; }
function provPolicy(p)  { return p.disabled_by_policy === true || p.status === 'disabled_by_policy'; }
function provDormant(p) { return !provLive(p) && !provPolicy(p); }   // dormant = key required, none set
function provReason(p)  { return p.reason || p.disabled_reason || ''; }

function _providerHealthCard(p) {
  const label = p.label || p.key || p.id || '';
  const live = provLive(p), policy = provPolicy(p);
  const cls = live ? 'badge-safe' : policy ? 'badge-disabled' : 'badge-warn';
  const statusText = live ? 'live' : policy ? 'off by policy' : 'needs key';
  const reason = provReason(p);
  return '<div class="stat-card stat-card--provider">'
    + '<div class="stat-card__label">' + esc(label) + '</div>'
    + '<div class="stat-card__value"><span class="badge ' + cls + '">' + statusText + '</span></div>'
    + (reason ? '<div class="stat-card__sub" style="font-size:0.7rem;color:var(--c-muted)">' + esc(reason.slice(0, 70)) + '</div>' : '')
    + '</div>';
}

async function loadBudgetView() {
  const el = mount(); if (!el) return;
  el.innerHTML = (typeof skeletonCards === 'function')
    ? '<div class="state-loading state-loading--spin">Loading engine status…</div>' + skeletonCards(4, 'provider')
    : '<p class="state-loading">Loading engine status…</p>';

  const [provData, usageData, healthData] = await Promise.all([
    safeFetch('/api/providers'),
    safeFetch('/api/usage'),
    safeFetch('/api/health'),
  ]);

  const providers = provData ? (provData.providers || []) : [];
  const pList = Array.isArray(providers) ? providers : Object.values(providers);
  const liveProviders = pList.filter(provLive);
  const dormantProviders = pList.filter(provDormant);
  const offProviders = pList.filter(provPolicy);

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
