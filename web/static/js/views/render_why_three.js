/* views/render_why_three.js — decision layer. Ranks the top picks from your
   most recent discovery batch by real match score (review score breaks ties).
   Never invents a ranking; if fewer than 3 scored candidates exist it says so. */

function _scoreOf(j) {
  const m = pick(j, ['match', 'match_score'], null);
  return m == null ? null : Number(m);
}

function _whyCard(j, i) {
  const score = _scoreOf(j);
  const review = pick(j, ['review_score'], null);
  const company = esc(cleanText(pick(j, ['company', 'company_name', 'restaurant_name'], null), 'Company not listed'));
  const title = esc(cleanText(pick(j, ['title', 'job_title'], null), 'Untitled role'));
  const loc = esc(cleanText(pick(j, ['resolved_address', 'location'], null), 'Location not resolved'));
  const src = esc(cleanText(pick(j, ['source', '_provider', 'via'], null), ''));
  const commute = j.commute_seconds != null ? esc(formatMins(j.commute_seconds)) : null;
  const radius = j.radius_miles != null ? esc(formatMiles(j.radius_miles)) : null;
  const bits = [];
  if (score != null) bits.push('match ' + score);
  if (review != null) bits.push('review ' + review);
  if (commute) bits.push(commute + ' commute');
  if (radius) bits.push(radius);
  if (src) bits.push('via ' + src);
  return '<div class="why-card"><div class="why-card__rank">#' + (i + 1) + '</div>'
    + '<div class="why-card__title">' + title + ' — ' + company + '</div>'
    + '<div class="why-card__reason">' + esc(loc) + '</div>'
    + (bits.length ? '<div class="why-card__score">' + esc(bits.join(' · ')) + '</div>' : '')
    + '</div>';
}

async function loadWhyThreeView() {
  const el = mount(); if (!el) return;
  el.innerHTML = (typeof skeletonCards === 'function')
    ? '<div class="state-loading state-loading--spin">Ranking your last batch…</div>' + skeletonCards(3, 'job')
    : '<p class="state-loading">Ranking…</p>';

  const batchList = await safeFetch('/api/batches');
  const batches = arr(batchList, ['batches']);
  let jobs = [];
  if (batches.length) {
    const snap = await safeFetch('/api/batches/' + encodeURIComponent(batches[0].id || batches[0]));
    jobs = arr(snap, ['data', 'jobs', 'accepted', 'results']);
  }

  const header = sectionHeader({
    icon: 'why-three', kicker: 'Decision layer',
    title: 'Why these rank',
    blurb: 'The top picks from your most recent discovery batch, ranked by the real match score the engine computed. Ranked from stored data — not a live search.',
  });
  let html = header;

  const scored = jobs.filter(function (j) { return _scoreOf(j) != null; })
    .sort(function (a, b) {
      const d = _scoreOf(b) - _scoreOf(a);
      if (d !== 0) return d;
      return (Number(pick(b, ['review_score'], 0)) || 0) - (Number(pick(a, ['review_score'], 0)) || 0);
    });

  if (!scored.length) {
    html += emptyArt({ icon: 'why-three', title: 'No scored candidates yet',
      body: jobs.length
        ? 'Your last batch has jobs but none carry a match score yet. Run a fresh discovery to compute rankings.'
        : 'Run a discovery batch — once there are scored candidates, the top picks and their evidence appear here.',
      action: { label: 'Open Discovery', go: 'discovery' } });
  } else {
    const top = scored.slice(0, 3);
    html += '<h2 class="section-heading">Top ' + top.length + ' pick' + (top.length === 1 ? '' : 's') + '</h2>'
      + '<div class="stagger-in">' + top.map(_whyCard).join('') + '</div>';
    if (scored.length < 3) {
      html += '<div class="info-box">Only ' + scored.length + ' scored candidate'
        + (scored.length === 1 ? '' : 's') + ' in the last batch — run more discovery for a fuller ranking.</div>';
    } else {
      html += '<p class="status-line">Ranked from ' + scored.length + ' scored candidates in the latest batch.</p>';
    }
  }

  el.innerHTML = html;
  wireGo(el);
  JHP_SYNC.remember('why-three', { ranked: scored.length });
}

registerView('why-three', 'Why Three', loadWhyThreeView);
