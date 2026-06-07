document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('toggle-filters');
  const drawer = document.getElementById('filter-drawer');
  const closeBtn = document.getElementById('close-filters');
  const backdrop = document.getElementById('drawer-backdrop');
  const sidebar = document.getElementById('sidebar');
  const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
  const evidenceDrawer = document.getElementById('evidence-drawer');
  const closeEvidenceBtn = document.getElementById('close-evidence');

  function toggleBackdrop(show) {
    if (backdrop) {
      backdrop.classList.toggle('active', show);
    }
  }

  function toggleDrawer(open) {
    const isOpen = open !== undefined ? open : !drawer.classList.contains('open');
    drawer.classList.toggle('open', isOpen);
    toggleBtn.setAttribute('aria-expanded', isOpen);
    toggleBackdrop(isOpen);

    if (isOpen) {
      const firstInput = drawer.querySelector('select, input, button:not(#close-filters)');
      if (firstInput) firstInput.focus();
    } else {
      toggleBtn.focus();
    }
  }

  function toggleSidebar(open) {
    const isOpen = open !== undefined ? open : !sidebar.classList.contains('open');
    sidebar.classList.toggle('open', isOpen);
    toggleBackdrop(isOpen);
  }

  function toggleEvidence(open) {
    const isOpen = open !== undefined ? open : !evidenceDrawer.classList.contains('open');
    evidenceDrawer.classList.toggle('open', isOpen);
    evidenceDrawer.setAttribute('aria-hidden', !isOpen);
    toggleBackdrop(isOpen);
  }

  if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', () => toggleSidebar());
  }

  if (backdrop) {
    backdrop.addEventListener('click', () => {
      toggleDrawer(false);
      toggleSidebar(false);
      toggleEvidence(false);
    });
  }

  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-tab');
      AppState.setTab(target);
      if (window.innerWidth <= 1024) {
        toggleSidebar(false);
      }
    });
  });

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const lang = btn.getAttribute('data-lang');
      AppState.setLang(lang);
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

  toggleBtn.addEventListener('click', () => toggleDrawer());
  if (closeBtn) {
    closeBtn.addEventListener('click', () => toggleDrawer(false));
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
      if (sidebar.classList.contains('open')) {
        toggleSidebar(false);
      }
      if (evidenceDrawer.classList.contains('open')) {
        toggleEvidence(false);
      }
      const palette = document.getElementById('command-palette');
      if (palette.style.display !== 'none') {
        palette.style.display = 'none';
      }
    }

    // Ctrl+K for Command Palette
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      const palette = document.getElementById('command-palette');
      palette.style.display = palette.style.display === 'none' ? 'block' : 'none';
      if (palette.style.display !== 'none') {
        document.getElementById('cmd-input').focus();
        renderCommands();
      }
    }
  });

  window.commands = [
    { label: 'Go to Overview', action: () => AppState.setTab('overview') },
    { label: 'Go to Live Jobs', action: () => AppState.setTab('live_jobs') },
    { label: 'Go to Opportunities', action: () => AppState.setTab('opportunities') },
    { label: 'Go to History', action: () => AppState.setTab('history') },
    { label: 'Go to Budget', action: () => AppState.setTab('budget') },
    { label: 'Set Language to English', action: () => AppState.setLang('en') },
    { label: 'Set Language to Spanish', action: () => AppState.setLang('es') },
    { label: 'Set Language to Russian', action: () => AppState.setLang('ru') }
  ];

  function renderCommands(filter = '') {
    const results = document.getElementById('cmd-results');
    const filtered = window.commands.filter(c => c.label.toLowerCase().includes(filter.toLowerCase()));
    
    results.innerHTML = '';
    filtered.forEach(c => {
      const btn = document.createElement('button');
      btn.className = 'nav-tab';
      btn.style.width = '100%';
      btn.style.textAlign = 'left';
      btn.style.border = '1px solid transparent';
      btn.textContent = c.label;
      btn.onclick = () => {
        c.action();
        document.getElementById('command-palette').style.display = 'none';
      };
      results.appendChild(btn);
    });
  }

  document.getElementById('cmd-input').addEventListener('input', (e) => {
    renderCommands(e.target.value);
  });

  AppState.setTab('overview');
});
