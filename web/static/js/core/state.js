/* core/state.js — single source of app state + the view registry.
   No hardcoded jobs/counts; only UI state lives here. */

const AppState = {
  activeView: 'jobs',
  filters: {},
  lang: 'en',
  cache: {},        // viewId -> last payload (powers offline + command palette)
};

// Registered views: id -> { id, label, load }
const Views = {};

function registerView(id, label, loadFn) {
  Views[id] = { id, label, load: loadFn };
}

// Convenience: the main content mount node
function mount() {
  return document.getElementById('view-mount');
}
