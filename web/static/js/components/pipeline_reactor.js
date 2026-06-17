/* components/pipeline_reactor.js — live pipeline visualization over SSE.
   Connects ONLY if the backend exposes /api/pipeline/stream. Until then it
   renders an honest "stream unavailable" state — it never animates fake counts. */

const PIPELINE_STAGES = ['discover', 'normalize', 'resolve_place', 'classify', 'score', 'filter', 'dedupe', 'store'];

function renderReactorShell() {
  return '<div class="reactor" aria-label="Pipeline stages">'
    + PIPELINE_STAGES.map(function (s) { return '<span class="reactor-node" data-stage="' + esc(s) + '">' + esc(s) + ' <b class="reactor-node__n">—</b></span>'; }).join('')
    + '</div><p class="status-line reactor-status">Stream idle.</p>';
}

// Attempt a real SSE connection; degrade honestly if absent.
function connectPipeline(container) {
  if (!('EventSource' in window)) {
    const st = container.querySelector('.reactor-status');
    if (st) st.textContent = 'Live stream unavailable (no EventSource support). Showing last batch evidence in Debug.';
    return null;
  }
  let es;
  try { es = new EventSource('/api/pipeline/stream'); }
  catch (e) { return _reactorUnavailable(container); }

  es.onmessage = function (ev) {
    let data; try { data = JSON.parse(ev.data); } catch (_) { return; }
    const node = container.querySelector('.reactor-node[data-stage="' + (data.stage || '') + '"]');
    if (node) {
      node.classList.add('is-active');
      const n = node.querySelector('.reactor-node__n');
      if (n && data.count != null) n.textContent = String(data.count);
      if (typeof announce === 'function') announce(data.stage + ': ' + (data.count != null ? data.count : ''));
    }
  };
  es.onerror = function () { _reactorUnavailable(container); es.close(); };
  return es;
}

function _reactorUnavailable(container) {
  const st = container.querySelector('.reactor-status');
  if (st) st.textContent = 'Pipeline stream unavailable — the backend does not expose /api/pipeline/stream yet.';
  return null;
}
