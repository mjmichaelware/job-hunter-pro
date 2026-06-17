/* components/evidence_drawer.js — builds the per-job evidence panel and opens it
   in the spring bottom sheet. Every field is null-guarded; review_intelligence.*
   that FAST_JOBS gated off renders "unavailable", never a fabricated value. */

function buildEvidenceHtml(job) {
  const raw = pick(job, ['raw_title', 'title'], '');
  const company = pick(job, ['company', 'company_name', 'restaurant_name'], '');
  const trackId = pick(job, ['source_url', 'url', 'job_id', 'id'], raw + '|' + company);

  return '<table class="evidence-table">'
    + evidenceRow('Raw title', pick(job, ['raw_title'], null))
    + evidenceRow('Normalized title', pick(job, ['title', 'job_title'], null))
    + evidenceRow('Company', pick(job, ['company', 'company_name', 'restaurant_name'], null))
    + evidenceRow('Place ID', pick(job, ['place_id'], null))
    + evidenceRow('Resolved address', pick(job, ['resolved_address', 'normalized_address', 'location'], null))
    + evidenceRow('Source provider', pick(job, ['source', '_provider', 'provider', 'via'], null))
    + evidenceRow('Query used', pick(job, ['_query_used', 'place_query_used'], null))
    + evidenceRow('Source URL', pick(job, ['source_url', 'url'], null))
    + evidenceRow('Commute', job.commute_seconds != null ? formatMins(job.commute_seconds) : null)
    + evidenceRow('Radius', job.radius_miles != null ? formatMiles(job.radius_miles) : null)
    + evidenceRow('Match score', pick(job, ['match', 'match_score'], null))
    + evidenceRow('Review score', pick(job, ['review_score'], null))
    + evidenceRow('Consistency score', pick(job, ['consistency_score'], null))
    + evidenceRow('Risk level', pick(job, ['risk_level'], null))
    + evidenceRow('Google rating', pick(job, ['google_rating'], null))
    + evidenceRow('Google reviews', pick(job, ['google_review_count'], null))
    + evidenceRow('Role family', pick(job, ['role_family'], null))
    + evidenceRow('Tags', Array.isArray(job.tags) ? job.tags.join(', ') : null)
    + evidenceRow('Resolution flags', Array.isArray(job.resolution_flags) ? job.resolution_flags.join(', ') : null)
    + evidenceRow('Needs resolution', job.needs_resolution != null ? String(job.needs_resolution) : null)
    + '</table>'
    + '<button type="button" class="btn btn-track" data-job-id="' + esc(trackId) + '">' + esc(t('common.track')) + '</button>';
}

function openEvidence(job) {
  const title = pick(job, ['title', 'job_title', 'name'], 'Job evidence');
  openSheet(title, buildEvidenceHtml(job), function (body) {
    const trackBtn = body.querySelector('.btn-track');
    if (trackBtn) trackBtn.addEventListener('click', function () { trackJob(trackBtn); });
  });
}

async function trackJob(btn) {
  const jobId = btn.dataset.jobId;
  if (!jobId) return;
  btn.disabled = true; btn.textContent = 'Tracking…';
  try {
    const res = await fetch('/api/applications', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId, status: 'DISCOVERED', notes: '' }),
    });
    if (res.ok || res.status === 409) { btn.textContent = res.status === 409 ? 'Already tracked' : 'Tracked'; }
    else { btn.textContent = 'Track failed'; btn.disabled = false; }
  } catch (e) { btn.textContent = 'Track failed'; btn.disabled = false; }
}
