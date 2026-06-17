// Imports will be added here once render_overview and render_why_three are created
const AppState = {
  activeTab: 'live_jobs',
  budgetState: 'safe',
  lang: 'en',
  translations: {
    en: {
      overview: 'Overview',
      live_jobs: 'Live Jobs',
      opportunities: 'Opportunities',
      history: 'History',
      debug_evidence: 'Debug Evidence',
      providers: 'Providers',
      budget: 'Budget',
      why_three: 'Why Three'
    },
    es: {
      overview: 'Resumen',
      live_jobs: 'Empleos en vivo',
      opportunities: 'Oportunidades',
      history: 'Historial',
      debug_evidence: 'Evidencia',
      providers: 'Proveedores',
      budget: 'Presupuesto',
      why_three: '¿Por qué tres?'
    },
    ru: {
      overview: 'Обзор',
      live_jobs: 'Вакансии',
      opportunities: 'Возможности',
      history: 'История',
      debug_evidence: 'Отладка',
      providers: 'Провайдеры',
      budget: 'Бюджет',
      why_three: 'Почему три?'
    }
  },
  setLang(lang) {
    this.lang = lang;
    document.querySelectorAll('.lang-btn').forEach(b => {
      b.classList.toggle('active', b.getAttribute('data-lang') === lang);
    });
    this.translateUI();
  },
  translateUI() {
    const t = this.translations[this.lang];
    document.querySelectorAll('.nav-tab').forEach(btn => {
      const key = btn.getAttribute('data-tab');
      if (t[key]) btn.textContent = t[key];
    });
    // Add more translation targets if needed
  },
  filters: {
    // Always visible.
    // radius and matchScore default to '' (no narrowing) so the UI shows ALL
    // valid jobs by default. They only narrow when the user explicitly sets them.
    mode: '',
    radius: '',
    industry: '',
    provider: '',
    status: '',
    sort: 'newest',
    matchScore: '',

    // Advanced
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
  },
  cachedData: {
    health: null,
    usage: null,
    jobs: null,
    opportunities: null,
    history: null,
    providers: null,
    whyThree: null
  },
  setTab(tabId) {
    this.activeTab = tabId;
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));

    const activeBtn = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
    const activePanel = document.getElementById(`tab-${tabId}`);

    if (activeBtn) activeBtn.classList.add('active');
    if (activePanel) activePanel.classList.add('active');

    if (document.startViewTransition) {
      document.startViewTransition(() => { });
    }

    this.syncTabUI(tabId);
  },
  async syncTabUI(tabId) {
    const triggerBtn = document.getElementById('trigger-discovery-btn');
    const prepareBtn = document.getElementById('prepare-discovery-btn');
    const guard = document.getElementById('live-action-guard');

    if (tabId === 'live_jobs' || tabId === 'budget') {
      prepareBtn.style.display = 'inline-flex';
    } else {
      prepareBtn.style.display = 'none';
      guard.style.display = 'none';
    }

    if (prepareBtn && !prepareBtn.onclick) {
      prepareBtn.onclick = () => {
        prepareBtn.style.display = 'none';
        guard.style.display = 'flex';
      };
    }

    const cancelBtn = document.getElementById('cancel-discovery-btn');
    if (cancelBtn && !cancelBtn.onclick) {
      cancelBtn.onclick = () => {
        guard.style.display = 'none';
        prepareBtn.style.display = 'inline-flex';
      };
    }

    if (triggerBtn && !triggerBtn.onclick) {
      triggerBtn.onclick = async () => {
        console.log('Confirmed live discovery trigger');
        // This will be handled in later stages, for now just hide the guard
        guard.style.display = 'none';
        prepareBtn.style.display = 'inline-flex';
        
        if (typeof loadJobs === 'function') await loadJobs({ live: true, forceRefresh: true });
      };
    }

    // Dynamically call rendering functions based on the active tab
    switch (tabId) {
      case 'overview':
        if (typeof loadOverview === 'function') await loadOverview();
        break;
      case 'live_jobs':
        // loadJobs() defaults to live and session-caches, so revisits don't re-spend.
        if (typeof loadJobs === 'function') await loadJobs();
        break;
      case 'opportunities':
        if (typeof loadOpportunities === 'function') await loadOpportunities();
        break;
      case 'history':
        if (typeof loadHistory === 'function') await loadHistory();
        break;
      case 'debug_evidence':
        if (typeof loadDebugEvidence === 'function') await loadDebugEvidence();
        break;
      case 'providers':
        if (typeof loadProviders === 'function') await loadProviders();
        break;
      case 'budget':
        if (typeof loadBudget === 'function') await loadBudget();
        break;
      case 'why_three':
        if (typeof loadWhyThree === 'function') await loadWhyThree();
        break;
    }

    if (typeof loadCharts === 'function') await loadCharts();
  },
  showEvidence(id, type) {
    let data = null;
    const items = UI.getArray(this.cachedData[type === 'job' ? 'jobs' : 'opportunities']);
    data = items.find(item => (item.job_id || item.place_id || item.id) == id);

    if (data && typeof renderEvidence === 'function') {
      const card = document.querySelector(`.clickable-card[data-id="${id}"]`);
      if (card) {
        card.style.viewTransitionName = 'active-evidence-card';
      }

      const openDrawer = () => {
        renderEvidence(data, type);
        const drawer = document.getElementById('evidence-drawer');
        const backdrop = document.getElementById('drawer-backdrop');
        
        drawer.classList.add('open');
        drawer.setAttribute('aria-hidden', 'false');
        if (backdrop) backdrop.classList.add('active');
        
        const closeBtn = document.getElementById('close-evidence');
        if (closeBtn) closeBtn.focus();
        
        if (card) {
          card.style.viewTransitionName = '';
        }
      };

      if (document.startViewTransition) {
        document.startViewTransition(() => openDrawer());
      } else {
        openDrawer();
      }
    }
  }
};

/* S10-D canonical filter aliases.
   These preserve Document 6 camelCase filter keys while allowing existing UI
   controls to keep their current internal names. Do not remove without updating
   the S10-D proof gate. */
(function syncS10DCanonicalFilterState() {
  const root = typeof AppState !== 'undefined' ? AppState : (window.AppState = window.AppState || {});
  root.filters = root.filters || {};

  const defaults = {
    searchMode: root.filters.searchMode ?? root.filters.mode ?? 'cached',
    minMatchScore: root.filters.minMatchScore ?? root.filters.matchScore ?? root.filters.score ?? '',
    maxWalkMinutes: root.filters.maxWalkMinutes ?? root.filters.walkMinutes ?? '',
    maxTransitMinutes: root.filters.maxTransitMinutes ?? root.filters.transitMinutes ?? '',
    minReviewScore: root.filters.minReviewScore ?? root.filters.reviewScore ?? '',
    providerIncludeExclude: root.filters.providerIncludeExclude ?? root.filters.providerMode ?? 'include',
    classificationConfidence: root.filters.classificationConfidence ?? root.filters.confidence ?? ''
  };

  Object.entries(defaults).forEach(([key, value]) => {
    if (root.filters[key] === undefined) root.filters[key] = value;
  });
})();
