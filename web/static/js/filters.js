/* S10-D canonical filter schema.
   The UI may expose friendlier labels, but these are the Document 6 canonical
   keys that must remain stable across renderers, chips, and proof gates. */
const S10D_FILTER_SCHEMA = Object.freeze([
  'searchMode',
  'radius',
  'industry',
  'provider',
  'status',
  'sort',
  'minMatchScore',
  'maxWalkMinutes',
  'maxTransitMinutes',
  'minRating',
  'minReviewScore',
  'jobType',
  'payHint',
  'remoteOnsite',
  'providerIncludeExclude',
  'batch',
  'timeRange',
  'rejectionReason',
  'classificationConfidence',
  'placeStatus',
  'applicationState',
  'duplicateState'
]);

const S10D_FILTER_ALIASES = Object.freeze({
  searchMode: ['mode'],
  minMatchScore: ['matchScore', 'score'],
  maxWalkMinutes: ['walkMinutes'],
  maxTransitMinutes: ['transitMinutes'],
  minReviewScore: ['reviewScore'],
  providerIncludeExclude: ['providerMode'],
  classificationConfidence: ['confidence']
});

document.addEventListener('DOMContentLoaded', () => {
  const controls = [
    { main: 'filter-mode', drawer: 'drawer-filter-mode', key: 'mode' },
    { main: 'filter-industry', drawer: 'drawer-filter-industry', key: 'industry' },
    { main: 'filter-provider', drawer: 'drawer-filter-provider', key: 'provider' },
    { main: 'filter-status', drawer: 'drawer-filter-status', key: 'status' },
    { main: 'filter-sort', drawer: 'drawer-filter-sort', key: 'sort' },
    { main: 'filter-radius', drawer: 'drawer-filter-radius', key: 'radius', valEls: ['radius-val', 'drawer-radius-val'] },
    { main: 'filter-match', drawer: 'drawer-filter-match', key: 'matchScore', valEls: ['match-val', 'drawer-match-val'] },
    { el: 'filter-walk', key: 'maxWalk', valEl: 'walk-val' },
    { el: 'filter-transit', key: 'maxTransit', valEl: 'transit-val' },
    { el: 'filter-rating', key: 'minRating', valEl: 'rating-val' },
    { el: 'filter-review', key: 'minReview', valEl: 'review-val' },
    { el: 'filter-job-type', key: 'jobType' },
    { el: 'filter-pay', key: 'payHint' },
    { el: 'filter-remote', key: 'remoteOnsite' },
    { el: 'filter-batch', key: 'batchId' },
    { el: 'filter-time', key: 'timeRange' },
    { el: 'filter-rejection', key: 'rejectionReason' },
    { el: 'filter-confidence', key: 'confidence', valEl: 'conf-val' },
    { el: 'filter-place-status', key: 'placeStatus' },
    { el: 'filter-app-state', key: 'applicationState' },
    { el: 'filter-duplicate', key: 'duplicateState' }
  ];

  controls.forEach(ctrl => {
    const mainEl = ctrl.main ? document.getElementById(ctrl.main) : document.getElementById(ctrl.el);
    const drawerEl = ctrl.drawer ? document.getElementById(ctrl.drawer) : null;

    const setupListener = (el) => {
      if (!el) return;
      const eventType = el.type === 'range' ? 'input' : (el.type === 'text' ? 'input' : 'change');
      el.addEventListener(eventType, (e) => {
        let val = e.target.value;
        if (el.type === 'range') val = parseFloat(val);

        // radius/matchScore at 0 means "Any" -> no narrowing (store '').
        const isAnyZero = (ctrl.key === 'radius' || ctrl.key === 'matchScore') && (!val || Number(val) <= 0);
        AppState.filters[ctrl.key] = isAnyZero ? '' : val;

        let display = val;
        if (ctrl.key === 'radius') display = isAnyZero ? 'Any' : `${val}mi`;
        else if (ctrl.key === 'matchScore') display = isAnyZero ? 'Any' : `${val}%`;

        // Sync other elements
        if (mainEl && mainEl !== el) mainEl.value = val;
        if (drawerEl && drawerEl !== el) drawerEl.value = val;

        // Sync value displays
        if (ctrl.valEls) {
          ctrl.valEls.forEach(vid => {
            const vdisplay = document.getElementById(vid);
            if (vdisplay) vdisplay.textContent = display;
          });
        }
        if (ctrl.valEl) {
          const vdisplay = document.getElementById(ctrl.valEl);
          if (vdisplay) vdisplay.textContent = display;
        }

        applyLocalFilters();
        renderFilterChips();
      });
    };

    setupListener(mainEl);
    setupListener(drawerEl);
  });

  const resetBtn = document.getElementById('reset-all-filters');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      resetFilters();
    });
  }

  // Initial render
  renderFilterChips();
});

function resetFilters() {
  const defaults = {
    mode: '',
    radius: '',
    industry: '',
    provider: '',
    status: '',
    sort: 'newest',
    matchScore: '',
    maxWalk: 30,
    maxTransit: 60,
    minRating: 0,
    minReview: 0,
    jobType: '',
    payHint: '',
    remoteOnsite: '',
    providerExclude: [],
    batchId: '',
    timeRange: 'all',
    rejectionReason: '',
    confidence: 0,
    placeStatus: '',
    applicationState: '',
    duplicateState: ''
  };

  Object.assign(AppState.filters, defaults);
  
  // Sync UI
  const idMaps = [
    { key: 'mode', ids: ['filter-mode', 'drawer-filter-mode'] },
    { key: 'radius', ids: ['filter-radius', 'drawer-filter-radius'], vids: ['radius-val', 'drawer-radius-val'] },
    { key: 'industry', ids: ['filter-industry', 'drawer-filter-industry'] },
    { key: 'provider', ids: ['filter-provider', 'drawer-filter-provider'] },
    { key: 'status', ids: ['filter-status', 'drawer-filter-status'] },
    { key: 'sort', ids: ['filter-sort', 'drawer-filter-sort'] },
    { key: 'matchScore', ids: ['filter-match', 'drawer-filter-match'], vids: ['match-val', 'drawer-match-val'] },
    { key: 'maxWalk', ids: ['filter-walk'], vids: ['walk-val'] },
    { key: 'maxTransit', ids: ['filter-transit'], vids: ['transit-val'] },
    { key: 'minRating', ids: ['filter-rating'], vids: ['rating-val'] },
    { key: 'minReview', ids: ['filter-review'], vids: ['review-val'] },
    { key: 'jobType', ids: ['filter-job-type'] },
    { key: 'payHint', ids: ['filter-pay'] },
    { key: 'remoteOnsite', ids: ['filter-remote'] },
    { key: 'batchId', ids: ['filter-batch'] },
    { key: 'timeRange', ids: ['filter-time'] },
    { key: 'rejectionReason', ids: ['filter-rejection'] },
    { key: 'confidence', ids: ['filter-confidence'], vids: ['conf-val'] },
    { key: 'placeStatus', ids: ['filter-place-status'] },
    { key: 'applicationState', ids: ['filter-app-state'] },
    { key: 'duplicateState', ids: ['filter-duplicate'] }
  ];

  idMaps.forEach(map => {
    const raw = AppState.filters[map.key];
    // radius/matchScore reset to "Any" (slider 0, no narrowing).
    const isAny = (map.key === 'radius' || map.key === 'matchScore') && (raw === '' || raw === null || Number(raw) <= 0);
    const sliderVal = isAny ? 0 : raw;
    let display = raw;
    if (map.key === 'radius') display = isAny ? 'Any' : `${raw}mi`;
    else if (map.key === 'matchScore') display = isAny ? 'Any' : `${raw}%`;

    map.ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = sliderVal;
    });
    if (map.vids) {
      map.vids.forEach(vid => {
        const el = document.getElementById(vid);
        if (el) el.textContent = display;
      });
    }
  });

  applyLocalFilters();
  renderFilterChips();
}

function renderFilterChips() {
  const container = document.getElementById('active-filters-chips');
  const countBadge = document.getElementById('filter-count-badge');
  const resetBtn = document.getElementById('reset-all-filters');
  
  if (!container) return;

  const defaults = {
    mode: '',
    radius: '',
    industry: '',
    provider: '',
    status: '',
    sort: 'newest',
    matchScore: '',
    maxWalk: 30,
    maxTransit: 60,
    minRating: 0,
    minReview: 0,
    jobType: '',
    payHint: '',
    remoteOnsite: '',
    batchId: '',
    timeRange: 'all',
    rejectionReason: '',
    confidence: 0,
    placeStatus: '',
    applicationState: '',
    duplicateState: ''
  };

  const chips = [];
  let count = 0;

  Object.entries(AppState.filters).forEach(([key, val]) => {
    if (val !== defaults[key] && val !== '' && val !== null && (Array.isArray(val) ? val.length > 0 : true)) {
      count++;
      chips.push(`<div class="badge badge-cached" style="display:flex; align-items:center; gap:var(--space-xs);">
        <span>${key}: ${val}</span>
        <span style="cursor:pointer; font-weight:bold;" onclick="removeFilter('${key}')">✕</span>
      </div>`);
    }
  });

  container.innerHTML = chips.join('');
  
  if (countBadge) {
    countBadge.textContent = `${count} filters`;
    countBadge.style.display = count > 0 ? 'inline-flex' : 'none';
  }

  if (resetBtn) {
    // Always available so the user can guarantee "show all" at any time.
    resetBtn.style.display = 'inline-flex';
    resetBtn.textContent = count > 0 ? `Show All / Reset (${count})` : 'Show All / Reset';
  }
}

window.removeFilter = function(key) {
  const defaults = {
    mode: '',
    radius: '',
    industry: '',
    provider: '',
    status: '',
    sort: 'newest',
    matchScore: '',
    maxWalk: 30,
    maxTransit: 60,
    minRating: 0,
    minReview: 0,
    jobType: '',
    payHint: '',
    remoteOnsite: '',
    providerExclude: [],
    batchId: '',
    timeRange: 'all',
    rejectionReason: '',
    confidence: 0,
    placeStatus: '',
    applicationState: '',
    duplicateState: ''
  };

  AppState.filters[key] = defaults[key];
  
  // Sync UI (reuse logic from resetFilters for simplicity or just specific key)
  const idMaps = [
    { key: 'mode', ids: ['filter-mode', 'drawer-filter-mode'] },
    { key: 'radius', ids: ['filter-radius', 'drawer-filter-radius'], vids: ['radius-val', 'drawer-radius-val'] },
    { key: 'industry', ids: ['filter-industry', 'drawer-filter-industry'] },
    { key: 'provider', ids: ['filter-provider', 'drawer-filter-provider'] },
    { key: 'status', ids: ['filter-status', 'drawer-filter-status'] },
    { key: 'sort', ids: ['filter-sort', 'drawer-filter-sort'] },
    { key: 'matchScore', ids: ['filter-match', 'drawer-filter-match'], vids: ['match-val', 'drawer-match-val'] },
    { key: 'maxWalk', ids: ['filter-walk'], vids: ['walk-val'] },
    { key: 'maxTransit', ids: ['filter-transit'], vids: ['transit-val'] },
    { key: 'minRating', ids: ['filter-rating'], vids: ['rating-val'] },
    { key: 'minReview', ids: ['filter-review'], vids: ['review-val'] },
    { key: 'jobType', ids: ['filter-job-type'] },
    { key: 'payHint', ids: ['filter-pay'] },
    { key: 'remoteOnsite', ids: ['filter-remote'] },
    { key: 'batchId', ids: ['filter-batch'] },
    { key: 'timeRange', ids: ['filter-time'] },
    { key: 'rejectionReason', ids: ['filter-rejection'] },
    { key: 'confidence', ids: ['filter-confidence'], vids: ['conf-val'] },
    { key: 'placeStatus', ids: ['filter-place-status'] },
    { key: 'applicationState', ids: ['filter-app-state'] },
    { key: 'duplicateState', ids: ['filter-duplicate'] }
  ];

  const map = idMaps.find(m => m.key === key);
  if (map) {
    map.ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = defaults[key];
    });
    if (map.vids) {
      map.vids.forEach(vid => {
        const el = document.getElementById(vid);
        if (el) el.textContent = defaults[key];
      });
    }
  }

  applyLocalFilters();
  renderFilterChips();
};

function applyLocalFilters() {
  if (AppState.activeTab === 'live_jobs') renderJobsList(AppState.cachedData.jobs);
  if (AppState.activeTab === 'opportunities') renderOpportunitiesList(AppState.cachedData.opportunities);
}
