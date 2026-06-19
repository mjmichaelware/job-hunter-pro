/* core/a11y.js — focus management for dialogs/sheets + reduced-motion flag. */

const A11y = {
  prefersReducedMotion: function () {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  },

  // Trap Tab focus inside a container; returns a release() function.
  trapFocus: function (container) {
    if (!container) return function () {};
    const sel = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
    const prev = document.activeElement;
    function onKey(e) {
      if (e.key !== 'Tab') return;
      const nodes = Array.prototype.slice.call(container.querySelectorAll(sel)).filter(function (n) { return n.offsetParent !== null; });
      if (!nodes.length) return;
      const first = nodes[0], last = nodes[nodes.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
    container.addEventListener('keydown', onKey);
    const focusable = container.querySelector(sel);
    if (focusable) focusable.focus();
    return function release() {
      container.removeEventListener('keydown', onKey);
      if (prev && prev.focus) prev.focus();
    };
  },
};
