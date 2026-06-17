/* components/geo_radar.js — concentric radius rings + job pins.
   Renders pins ONLY when jobs carry real lat/lng (or radius_miles) data.
   With no geo data (FAST_JOBS mode) it shows an honest "unavailable" state —
   it never fabricates positions. */

function hasGeo(jobs) {
  return (jobs || []).some(function (j) {
    return (j.lat != null && j.lng != null) || j.radius_miles != null;
  });
}

function renderGeoRadar(jobs, maxRadius) {
  const list = jobs || [];
  if (!hasGeo(list)) {
    return '<div class="geo-radar geo-radar--na"><p class="state-empty">Geo radar unavailable — '
      + 'no resolved coordinates or radii in the current results (FAST_JOBS mode skips per-job geocoding).</p></div>';
  }
  const R = Number(maxRadius) || Math.max.apply(null, list.map(function (j) { return Number(j.radius_miles) || 0; })) || 5;
  const pins = list.filter(function (j) { return j.radius_miles != null; }).slice(0, 60).map(function (j) {
    const frac = Math.min(1, (Number(j.radius_miles) || 0) / R);
    const angle = (Math.random() * 360) | 0; // angle is unknown without lat/lng; distance is real
    const x = 50 + Math.cos(angle * Math.PI / 180) * frac * 46;
    const y = 50 + Math.sin(angle * Math.PI / 180) * frac * 46;
    const reach = (j.commute_seconds != null && j.commute_seconds / 60 <= 35) ? 'pin--ok' : 'pin--far';
    return '<span class="geo-pin ' + reach + '" style="left:' + x.toFixed(1) + '%;top:' + y.toFixed(1) + '%" title="' + esc(pick(j, ['title'], '')) + ' · ' + esc(formatMiles(j.radius_miles)) + '"></span>';
  }).join('');
  return '<div class="geo-radar"><div class="geo-rings"></div><span class="geo-origin"></span>' + pins
    + '<div class="geo-radar__cap">rings to ' + R.toFixed(1) + ' mi · distance is real, bearing is illustrative</div></div>';
}
