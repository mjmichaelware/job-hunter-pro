/* components/aria_announcer.js — voice real state changes to screen readers.
   Used for view loads, pipeline counts, offline transitions. Truth only. */

function announce(message, assertive) {
  const region = document.getElementById('aria-live');
  if (!region) return;
  region.setAttribute('aria-live', assertive ? 'assertive' : 'polite');
  // clear then set so repeated identical messages still announce
  region.textContent = '';
  window.setTimeout(function () { region.textContent = String(message == null ? '' : message); }, 30);
}
