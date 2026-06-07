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

  // Evidence Drawer toggle logic
  const evidenceDrawer = document.getElementById('evidence-drawer');
  const closeEvidenceBtn = document.getElementById('close-evidence');

  function toggleEvidence(open) {
    const isOpen = open !== undefined ? open : !evidenceDrawer.classList.contains('open');
    evidenceDrawer.classList.toggle('open', isOpen);
    evidenceDrawer.setAttribute('aria-hidden', !isOpen);
    
    if (!isOpen) {
      // Return focus to whatever triggered it? 
      // For now, let's just use the last focused element if we tracked it, 
      // but simple focus return to body or main-content is safer if we don't track.
    }
  }

  if (closeEvidenceBtn) {
    closeEvidenceBtn.addEventListener('click', () => toggleEvidence(false));
  }

  // Event Delegation for clickable cards (Job & Opportunities)
  document.addEventListener('click', (e) => {
    const card = e.target.closest('.clickable-card');
    if (card) {
      const id = card.getAttribute('data-id');
      const type = card.getAttribute('data-type');
      AppState.showEvidence(id, type);
    }
  });

  // Handle keyboard activation for cards
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      const card = e.target.closest('.clickable-card');
      if (card) {
        e.preventDefault();
        const id = card.getAttribute('data-id');
        const type = card.getAttribute('data-type');
        AppState.showEvidence(id, type);
      }
    }
  });

  // Close drawers on Escape key
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (drawer.classList.contains('open')) {
        toggleDrawer(false);
      }
      if (evidenceDrawer.classList.contains('open')) {
        toggleEvidence(false);
      }
    }
  });

  AppState.setTab('overview');
});