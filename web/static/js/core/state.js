/* core/state.js — single source of app state + the view registry.
   No hardcoded jobs/counts; only UI state lives here. */

const AppState = {
  activeView: 'home',
  filters: {},
  lang: 'en',
  layout: 'cols-1',   // list / cols-2 / cols-3 / cols-4 (layout_toggle.js)
  groupBy: 'none',    // none / industry / role (group_by.js)
  sort: 'match_desc', // sort.js
  cache: {},          // viewId -> last payload (powers offline + command palette)
};

// Registered views: id -> { id, label, load, hidden }
const Views = {};

// opts.hidden → registered (routable) but not shown in the nav rail (e.g. landing).
function registerView(id, label, loadFn, opts) {
  Views[id] = { id: id, label: label, load: loadFn, hidden: !!(opts && opts.hidden) };
}

// Convenience: the main content mount node
function mount() {
  return document.getElementById('view-mount');
}
