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
  // Always Visible
  const mode = document.getElementById('filter-mode');
  const industry = document.getElementById('filter-industry');
  const provider = document.getElementById('filter-provider');
  const status = document.getElementById('filter-status');
  const sort = document.getElementById('filter-sort');
  const radius = document.getElementById('filter-radius');
  const match = document.getElementById('filter-match');

  // Advanced Drawer
  const walk = document.getElementById('filter-walk');
  const transit = document.getElementById('filter-transit');
  const rating = document.getElementById('filter-rating');
  const review = document.getElementById('filter-review');
  const jobType = document.getElementById('filter-job-type');
  const pay = document.getElementById('filter-pay');
  const remote = document.getElementById('filter-remote');
  const batch = document.getElementById('filter-batch');
  const time = document.getElementById('filter-time');
  const rejection = document.getElementById('filter-rejection');
  const confidence = document.getElementById('filter-confidence');
  const placeStatus = document.getElementById('filter-place-status');
  const appState = document.getElementById('filter-app-state');
  const duplicate = document.getElementById('filter-duplicate');

  const controls = [
    { el: mode, key: 'mode' },
    { el: industry, key: 'industry' },
    { el: provider, key: 'provider' },
    { el: status, key: 'status' },
    { el: sort, key: 'sort' },
    { el: radius, key: 'radius', valEl: 'radius-val' },
    { el: match, key: 'matchScore', valEl: 'match-val' },
    { el: walk, key: 'maxWalk', valEl: 'walk-val' },
    { el: transit, key: 'maxTransit', valEl: 'transit-val' },
    { el: rating, key: 'minRating', valEl: 'rating-val' },
    { el: review, key: 'minReview', valEl: 'review-val' },
    { el: jobType, key: 'jobType' },
    { el: pay, key: 'payHint' },
    { el: remote, key: 'remoteOnsite' },
    { el: batch, key: 'batchId' },
    { el: time, key: 'timeRange' },
    { el: rejection, key: 'rejectionReason' },
    { el: confidence, key: 'confidence', valEl: 'conf-val' },
    { el: placeStatus, key: 'placeStatus' },
    { el: appState, key: 'applicationState' },
    { el: duplicate, key: 'duplicateState' }
  ];

  controls.forEach(ctrl => {
    if (!ctrl.el) return;

    const eventType = ctrl.el.type === 'range' ? 'input' : (ctrl.el.type === 'text' ? 'input' : 'change');

    ctrl.el.addEventListener(eventType, (e) => {
      let val = e.target.value;
      if (ctrl.el.type === 'range') val = parseFloat(val);
      
      AppState.filters[ctrl.key] = val;
      
      if (ctrl.valEl) {
        const display = document.getElementById(ctrl.valEl);
        if (display) display.textContent = val;
      }

      applyLocalFilters();
      renderFilterChips();
    });
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
    radius: 5,
    industry: '',
    provider: '',
    status: '',
    sort: 'newest',
    matchScore: 60,
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
  const ids = {
    mode: 'filter-mode',
    radius: 'filter-radius',
    industry: 'filter-industry',
    provider: 'filter-provider',
    status: 'filter-status',
    sort: 'filter-sort',
    matchScore: 'filter-match',
    maxWalk: 'filter-walk',
    maxTransit: 'filter-transit',
    minRating: 'filter-rating',
    minReview: 'filter-review',
    jobType: 'filter-job-type',
    payHint: 'filter-pay',
    remoteOnsite: 'filter-remote',
    batchId: 'filter-batch',
    timeRange: 'filter-time',
    rejectionReason: 'filter-rejection',
    confidence: 'filter-confidence',
    placeStatus: 'filter-place-status',
    applicationState: 'filter-app-state',
    duplicateState: 'filter-duplicate'
  };

  const valDisplays = {
    radius: 'radius-val',
    matchScore: 'match-val',
    maxWalk: 'walk-val',
    maxTransit: 'transit-val',
    minRating: 'rating-val',
    minReview: 'review-val',
    confidence: 'conf-val'
  };

  Object.entries(ids).forEach(([key, id]) => {
    const el = document.getElementById(id);
    if (el) {
      el.value = AppState.filters[key];
    }
  });

  Object.entries(valDisplays).forEach(([key, id]) => {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = AppState.filters[key];
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
    radius: 5,
    industry: '',
    provider: '',
    status: '',
    sort: 'newest',
    matchScore: 60,
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
    resetBtn.style.display = count > 0 ? 'inline-flex' : 'none';
  }
}

window.removeFilter = function(key) {
  const defaults = {
    mode: '',
    radius: 5,
    industry: '',
    provider: '',
    status: '',
    sort: 'newest',
    matchScore: 60,
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
  
  // Sync UI
  const idMap = {
    mode: 'filter-mode',
    radius: 'filter-radius',
    industry: 'filter-industry',
    provider: 'filter-provider',
    status: 'filter-status',
    sort: 'filter-sort',
    matchScore: 'filter-match',
    maxWalk: 'filter-walk',
    maxTransit: 'filter-transit',
    minRating: 'filter-rating',
    minReview: 'filter-review',
    jobType: 'filter-job-type',
    payHint: 'filter-pay',
    remoteOnsite: 'filter-remote',
    batchId: 'filter-batch',
    timeRange: 'filter-time',
    rejectionReason: 'filter-rejection',
    confidence: 'filter-confidence',
    placeStatus: 'filter-place-status',
    applicationState: 'filter-app-state',
    duplicateState: 'filter-duplicate'
  };

  const el = document.getElementById(idMap[key]);
  if (el) {
    el.value = defaults[key];
  }

  const valDisplays = {
    radius: 'radius-val',
    matchScore: 'match-val',
    maxWalk: 'walk-val',
    maxTransit: 'transit-val',
    minRating: 'rating-val',
    minReview: 'review-val',
    confidence: 'conf-val'
  };
  if (valDisplays[key]) {
    const display = document.getElementById(valDisplays[key]);
    if (display) display.textContent = defaults[key];
  }

  applyLocalFilters();
  renderFilterChips();
};

function applyLocalFilters() {
  if (AppState.activeTab === 'live_jobs') renderJobsList(AppState.cachedData.jobs);
  if (AppState.activeTab === 'opportunities') renderOpportunitiesList(AppState.cachedData.opportunities);
}
