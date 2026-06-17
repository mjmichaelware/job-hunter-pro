/* views/render_health.js — header health strip. Safe: /api/health only.
   Not a tab; called by the router on boot and when connectivity returns. */

async function renderHealth() {
  const strip = document.getElementById('health-strip');
  if (!strip) return;
  const health = await safeFetch('/api/health');
  if (!health) {
    strip.innerHTML = '<span class="badge badge-error">backend unreachable</span>';
    return;
  }
  const ver = esc(health.version || 'unknown');
  const ok = (health.status === 'ok' || health.status === 'healthy');
  const flags = [];
  if (health.serpapi_enabled != null) flags.push(dot('serp', health.serpapi_enabled));
  if (health.maps_enabled != null) flags.push(dot('maps', health.maps_enabled));
  if (health.origin_geocoded != null) flags.push(dot('geo', health.origin_geocoded));
  strip.innerHTML = '<span class="badge ' + (ok ? 'badge-safe' : 'badge-error') + '">' + esc(health.status || 'unknown') + '</span> '
    + flags.join(' ') + ' <span class="na">v' + ver + '</span>';

  // honest ambient modulation: calmer field when fewer providers are live
  if (typeof updateVolumetric === 'function') {
    const live = [health.serpapi_enabled, health.maps_enabled].filter(Boolean).length;
    updateVolumetric({ intensity: live / 2 });
  }
}

function dot(label, on) {
  return '<span class="badge ' + (on ? 'badge-safe' : 'badge-disabled') + '" title="' + esc(label) + '">' + esc(label) + '</span>';
}
