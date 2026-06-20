/* components/resume_context.js — loads the résumé once and computes an HONEST
   per-job fit: which of the user's real skills/languages/industries the job text
   actually mentions. No score is invented; an empty match renders as "no direct
   overlap", never a fake percentage. Exposes resumeFitHtml(job) for the drawer. */

var _resume = null;
var _resumeLoading = null;

function loadResume() {
  if (_resume) return Promise.resolve(_resume);
  if (_resumeLoading) return _resumeLoading;
  _resumeLoading = fetch('/static/assets/resume.json')
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (j) { _resume = j; return j; })
    .catch(function () { _resume = null; return null; });
  return _resumeLoading;
}

function _jobText(job) {
  return [pick(job, ['title', 'job_title'], ''), pick(job, ['description'], ''),
          pick(job, ['company', 'restaurant_name'], ''), (job.tags || []).join(' '),
          pick(job, ['role_family', 'industry'], '')].join(' ').toLowerCase();
}

// Returns { skills:[{label,tier}], industry:bool } — only real overlaps.
function resumeMatch(job) {
  if (!_resume) return null;
  const text = _jobText(job);
  const skills = (_resume.skills || []).filter(function (s) {
    return (s.keywords || []).some(function (k) { return text.indexOf(String(k).toLowerCase()) !== -1; });
  }).map(function (s) { return { label: s.label, tier: s.tier }; });
  const industry = (_resume.target_industries || []).some(function (i) {
    return text.indexOf(String(i).replace('_', ' ')) !== -1
        || text.indexOf(String(i).replace('_', '-')) !== -1;
  });
  return { skills: skills, industry: industry };
}

function resumeFitHtml(job) {
  if (!_resume) return '';
  const m = resumeMatch(job);
  if (!m) return '';
  const langs = (_resume.languages || []).map(function (l) {
    return '<span class="tag">' + esc(l.label) + ' ' + esc(l.level) + '</span>';
  }).join('');
  let inner;
  if (!m.skills.length && !m.industry) {
    inner = '<p class="na">No direct overlap with your résumé skills in this listing.</p>';
  } else {
    const chips = m.skills.map(function (s) {
      return '<span class="badge badge-safe">' + esc(s.label) + ' · ' + esc(s.tier) + '</span>';
    }).join('');
    inner = '<div class="resume-fit__chips">'
      + (m.industry ? '<span class="badge badge-cached">target industry</span>' : '')
      + chips + '</div>';
  }
  return '<div class="resume-sec"><h4 class="research-sec__title">Résumé fit · '
    + esc(_resume.name || 'you') + '</h4>' + inner
    + '<div class="resume-fit__langs">' + langs + '</div></div>';
}

if (typeof window !== 'undefined') { loadResume(); }
