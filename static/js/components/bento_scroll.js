document.addEventListener('DOMContentLoaded', () => {
  const setupKeyboardAccessibility = () => {
    document.querySelectorAll('.scroll-zone').forEach((zone, index) => {
      if (zone.querySelector('.data-table')) {
        if (!zone.hasAttribute('role')) {
          zone.setAttribute('role', 'region');
        }
        if (!zone.hasAttribute('aria-label')) {
          zone.setAttribute('aria-label', `Table scroll region ${index + 1}`);
        }
        if (!zone.hasAttribute('tabindex')) {
          zone.setAttribute('tabindex', '0');
        }
      }
    });
  };

  // Run immediately for any static tables
  setupKeyboardAccessibility();

  // Set up MutationObserver to detect dynamically added tables
  const observer = new MutationObserver(() => {
    setupKeyboardAccessibility();
  });
  observer.observe(document.body, { childList: true, subtree: true });
});

// Intercept smooth scrolling for users preferring reduced motion
(function() {
  const originalScrollIntoView = Element.prototype.scrollIntoView;
  Element.prototype.scrollIntoView = function(options) {
    if (options && options.behavior === 'smooth') {
      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReduced) {
        const safeOptions = Object.assign({}, options, { behavior: 'auto' });
        return originalScrollIntoView.call(this, safeOptions);
      }
    }
    return originalScrollIntoView.call(this, options);
  };
})();
