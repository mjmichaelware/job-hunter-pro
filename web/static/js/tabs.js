document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('toggle-filters');
  const drawer = document.getElementById('filter-drawer');
  const closeBtn = document.getElementById('close-filters');

  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-tab');
      AppState.setTab(target);
    });
  });

  function handleCardClick(card) {
    const target = card.getAttribute('data-target');
    AppState.setTab(target);
  }

  document.querySelectorAll('.card[data-target]').forEach(card => {
    card.addEventListener('click', () => handleCardClick(card));
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleCardClick(card);
      }
    });
  });

  function toggleDrawer(open) {
    const isOpen = open !== undefined ? open : !drawer.classList.contains('open');
    drawer.classList.toggle('open', isOpen);
    toggleBtn.setAttribute('aria-expanded', isOpen);

    if (isOpen) {
      // Move focus to the first interactive element in the drawer
      const firstInput = drawer.querySelector('select, input, button:not(#close-filters)');
      if (firstInput) firstInput.focus();
    } else {
      // Return focus to the toggle button
      toggleBtn.focus();
    }
  }

  toggleBtn.addEventListener('click', () => toggleDrawer());
  if (closeBtn) {
    closeBtn.addEventListener('click', () => toggleDrawer(false));
  }

  // Close drawer on Escape key
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && drawer.classList.contains('open')) {
      toggleDrawer(false);
    }
  });

  AppState.setTab('overview');
});