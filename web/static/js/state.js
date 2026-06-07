// Imports will be added here once render_overview and render_why_three are created
const AppState={activeTab:'overview',filters:{industry:'',radius:5,matchScore:60},cachedData:{health:null,usage:null,jobs:null,opportunities:null,history:null,providers:null,whyThree:null},setTab(tabId){this.activeTab=tabId;document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));document.querySelectorAll('.nav-tab').forEach(b=>b.classList.remove('active'));const activeBtn=document.querySelector(`.nav-tab[data-tab="${tabId}"]`);const activePanel=document.getElementById(`tab-${tabId}`);if(activeBtn)activeBtn.classList.add('active');if(activePanel)activePanel.classList.add('active');if(document.startViewTransition){document.startViewTransition(()=>{})}this.syncTabUI(tabId)},async syncTabUI(tabId){const triggerBtn=document.getElementById('trigger-discovery-btn');if(tabId==='live_jobs'||tabId==='budget'){triggerBtn.style.display='inline-flex'}else{triggerBtn.style.display='none'}
    // Dynamically call rendering functions based on the active tab
    switch (tabId) {
        case 'overview':
            if (typeof loadOverview === 'function') await loadOverview();
            break;
        case 'live_jobs':
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
    }}};