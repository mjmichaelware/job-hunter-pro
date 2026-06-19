/* visuals/halos.js — Markov vacancy-prediction halos (Beta).
   Strictly walled off: only activates if a real /api/predictions endpoint exists.
   Until then it is an honest no-op — it never invents prediction leads, never
   mixes into accepted jobs, never auto-applies. */

const PredictionHalos = {
  available: false,

  // Probe (no quota): if the backend ever exposes predictions, light up later.
  probe: async function () {
    const data = await safeFetch('/api/predictions');
    this.available = !!(data && (Array.isArray(data.predictions) || Array.isArray(data.data)));
    return this.available;
  },

  // Render is intentionally inert until a real predictions payload exists.
  render: function () {
    return '<p class="state-empty">Predicted leads are a Beta feature and are not enabled yet. '
      + 'Predictions are heuristics from public signals — never confirmed job listings.</p>';
  },
};
