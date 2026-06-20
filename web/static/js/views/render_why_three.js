/* views/render_why_three.js — Top Matches: highest-scoring accepted jobs from
   the most recent discovery batch, shown as full bento cards (top 12).
   Uses AppState.liveResult first when a live run just completed. */

async function loadWhyThreeView() {
  const el = mount(); if (!el) return;
  el.innerHTML = '<p class="state-loading">Loading top matches…</p>';

  // Prefer a just-completed live result; fall back to latest stored batch.
  let jobs = [];
  if (AppState && AppState.liveResult && Array.isArray(AppState.liveResult.jobs)) {
    jobs = AppState.liveResult.jobs;
  } else {
    const batchList = await safeFetch('/api/batches');
    const batches = arr(batchList, ['batches']);
    if (batches.length) {
      const snap = await safeFetch('/api/batches/' + encodeURIComponent(batches[0].id || batches[0]));
      jobs = arr(snap, ['data', 'jobs', 'accepted', 'results']);
    }
  }

  const header = sectionHeader({
    icon: 'spark', kicker: 'Best fits',
    title: 'Top Matches',
    blurb: 'Your highest-scoring accepted jobs from the latest discovery, ranked by match score. Sourced from stored batch data — no extra API calls.',
  });

  if (!jobs.length) {
    el.innerHTML = header;
    renderState(el, 'state-empty', 'No discovery results yet. Run a discovery to see your top matches.');
    return;
  }

  const topJobs = jobs
    .slice()
    .sort(function (a, b) {
      return (Number(pick(b, ['match', 'match_score'], 0)) || 0)
           - (Number(pick(a, ['match', 'match_score'], 0)) || 0);
    })
    .slice(0, 12);

  const container = document.createElement('div');
  container.className = 'bento-grid stagger-in';
  topJobs.forEach(function (job) {
    const cardHtml = bentoJobCard(job, false);
    const wrap = document.createElement('div');
    wrap.innerHTML = cardHtml;
    const card = wrap.firstElementChild;
    if (card) container.appendChild(card);
  });

  el.innerHTML = header;
  el.appendChild(container);
  wireBentoCards(container, topJobs);
  JHP_SYNC.remember('why-three', { ranked: topJobs.length });
}

registerView('why-three', 'Top Matches', loadWhyThreeView);
