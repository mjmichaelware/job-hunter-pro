/* components/industry_theme.js — sets <html data-industry> so the cockpit accent
   re-themes per the active hunt. Real signal only: driven by the industry filter
   or a single-industry batch. Mixed/unknown → clears back to base accent. */

const INDUSTRY_KEYS = ['food_service', 'hospitality', 'care_social', 'sales', 'customer_service', 'retail_ops'];

function applyIndustry(key) {
  const root = document.documentElement;
  if (key && INDUSTRY_KEYS.indexOf(key) !== -1) {
    root.setAttribute('data-industry', key);
  } else {
    root.removeAttribute('data-industry');
  }
}

// Given a list of jobs, theme by industry only if they're unanimous; else clear.
function applyIndustryFromJobs(jobs) {
  if (!Array.isArray(jobs) || !jobs.length) { applyIndustry(null); return; }
  let seen = null;
  for (const j of jobs) {
    const k = (j.industry || j.industry_key || '').toString();
    if (!k || INDUSTRY_KEYS.indexOf(k) === -1) continue;
    if (seen === null) seen = k;
    else if (seen !== k) { applyIndustry(null); return; }
  }
  applyIndustry(seen);
}
