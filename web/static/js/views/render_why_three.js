/* views/render_why_three.js — real limits explainer. Never invents a ranking;
   shows top-three only if the backend computed them. */

async function loadWhyThreeView() {
  const data = await safeFetch('/api/why-three');
  const el = mount(); if (!el) return;
  if (!data) { renderState(el, 'state-error', 'Could not load why-three data.'); return; }
  JHP_SYNC.remember('why-three', data);

  const headerHtml = sectionHeader({
    icon: 'why-three', kicker: 'Decision layer',
    title: 'Why these rank',
    blurb: 'When the engine has enough high-confidence matches, it surfaces the top picks with the evidence behind each ranking — never a fabricated score.',
  });
  let html = headerHtml;
  const reason = data.main_reason || data.message || data.explanation || null;
  if (reason) html += '<div class="info-box">' + esc(reason) + '</div>';

  const limits = data.current_limits || data.limits || null;
  if (limits && typeof limits === 'object') {
    html += '<h2 class="section-heading">Current limits</h2><table class="data-table"><tbody>'
      + Object.entries(limits).map(function (kv) { return '<tr><th>' + esc(kv[0]) + '</th><td>' + esc(String(kv[1])) + '</td></tr>'; }).join('')
      + '</tbody></table>';
  }

  const tips = arr(data, ['how_to_get_hundreds_without_burning_serpapi', 'tips', 'suggestions']);
  if (tips.length) {
    html += '<h2 class="section-heading">How to get more without burning quota</h2><ul style="padding-left:18px;color:var(--c-muted)">'
      + tips.map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('') + '</ul>';
  }

  const top3 = arr(data, ['top3', 'results']);
  if (top3.length) {
    html += '<h2 class="section-heading">Top candidates</h2>' + top3.map(function (it, i) {
      const score = pick(it, ['resonance_score', 'match', 'match_score'], null);
      const why = pick(it, ['why_included', 'reasoning', 'explanation'], null);
      return '<div class="why-card"><div class="why-card__rank">#' + (i + 1) + '</div>'
        + '<div class="why-card__title">' + esc(pick(it, ['title', 'job_title'], 'Untitled')) + ' — ' + esc(pick(it, ['company', 'company_name'], 'Unknown')) + '</div>'
        + (score != null ? '<div class="why-card__score">Score: ' + esc(String(score)) + '</div>' : '')
        + (why ? '<div class="why-card__reason">' + esc(why) + '</div>' : '') + '</div>';
    }).join('');
  }

  if (html === headerHtml) html += emptyArt({ icon: 'why-three', title: 'No ranking computed yet',
    body: 'Run a discovery batch — once there are enough scored candidates, the top picks and their evidence appear here.',
    action: { label: 'Open Discovery', go: 'discovery' } });
  el.innerHTML = html;
  wireGo(el);
}

registerView('why-three', 'Why Three', loadWhyThreeView);
