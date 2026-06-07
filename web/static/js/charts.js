const ChartUtils = {
  renderFallback(container, message = 'No data available to render chart.') {
    if (!container) return;
    container.innerHTML = `
      <div class="chart-fallback">
        ${UI.escape(message)}
        <div style="font-size:0.75rem; margin-top:8px; opacity:0.8;">Required data fields missing from API response. Table view remains authoritative.</div>
      </div>
    `;
  },

  createSVG(width = '100%', height = 200) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.setAttribute('viewBox', `0 0 400 ${height}`);
    svg.style.display = 'block';
    return svg;
  },

  renderPie(container, data = []) {
    if (!container) return;
    if (!data || data.length === 0) {
      this.renderFallback(container);
      return;
    }

    const total = data.reduce((sum, d) => sum + (d.value || 0), 0);
    if (total === 0) {
      this.renderFallback(container);
      return;
    }

    const svg = this.createSVG();
    const colors = ['#bb86fc', '#03dac6', '#cf6679', '#3700b3', '#018786'];
    let currentAngle = 0;
    const centerX = 150;
    const centerY = 100;
    const radius = 80;

    data.forEach((d, i) => {
      const sliceAngle = ((d.value || 0) / total) * 360;
      const x1 = centerX + radius * Math.cos((Math.PI * currentAngle) / 180);
      const y1 = centerY + radius * Math.sin((Math.PI * currentAngle) / 180);
      const x2 = centerX + radius * Math.cos((Math.PI * (currentAngle + sliceAngle)) / 180);
      const y2 = centerY + radius * Math.sin((Math.PI * (currentAngle + sliceAngle)) / 180);

      const largeArcFlag = sliceAngle > 180 ? 1 : 0;
      const pathData = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;

      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', pathData);
      path.setAttribute('fill', colors[i % colors.length]);
      path.setAttribute('stroke', 'var(--surface)');
      path.setAttribute('stroke-width', '2');
      svg.appendChild(path);

      // Legend
      const legendY = 30 + i * 25;
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', 260);
      rect.setAttribute('y', legendY);
      rect.setAttribute('width', 12);
      rect.setAttribute('height', 12);
      rect.setAttribute('fill', colors[i % colors.length]);
      svg.appendChild(rect);

      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', 280);
      text.setAttribute('y', legendY + 10);
      text.setAttribute('fill', 'var(--text)');
      text.setAttribute('font-size', '10px');
      text.textContent = `${d.label}: ${d.value}`;
      svg.appendChild(text);

      currentAngle += sliceAngle;
    });

    container.innerHTML = '';
    container.appendChild(svg);
  },

  renderFunnel(container, data = []) {
    if (!container) return;
    if (!data || data.length === 0) {
      this.renderFallback(container);
      return;
    }

    const svg = this.createSVG(400, 200);
    const maxVal = Math.max(...data.map(d => d.value || 0));
    if (maxVal === 0) {
      this.renderFallback(container);
      return;
    }

    data.forEach((d, i) => {
      const width = ((d.value || 0) / maxVal) * 300;
      const x = (400 - width) / 2;
      const y = 20 + i * 40;
      const height = 30;

      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', x);
      rect.setAttribute('y', y);
      rect.setAttribute('width', width);
      rect.setAttribute('height', height);
      rect.setAttribute('fill', 'var(--accent)');
      rect.setAttribute('opacity', 1 - i * 0.15);
      rect.setAttribute('rx', 4);
      svg.appendChild(rect);

      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('x', 200);
      label.setAttribute('y', y + 18);
      label.setAttribute('fill', '#000');
      label.setAttribute('font-size', '10px');
      label.setAttribute('font-weight', 'bold');
      label.setAttribute('text-anchor', 'middle');
      label.textContent = `${d.label}: ${d.value}`;
      svg.appendChild(label);
    });

    container.innerHTML = '';
    container.appendChild(svg);
  },

  renderBar(container, data = []) {
    if (!container) return;
    if (!data || data.length === 0) {
      this.renderFallback(container);
      return;
    }

    const svg = this.createSVG(400, 200);
    const maxVal = Math.max(...data.map(d => d.value || 0));
    if (maxVal === 0) {
      this.renderFallback(container);
      return;
    }

    const barWidth = 300 / data.length;
    data.forEach((d, i) => {
      const height = ((d.value || 0) / maxVal) * 150;
      const x = 50 + i * barWidth;
      const y = 170 - height;

      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', x + 5);
      rect.setAttribute('y', y);
      rect.setAttribute('width', barWidth - 10);
      rect.setAttribute('height', height);
      rect.setAttribute('fill', 'var(--accent)');
      rect.setAttribute('rx', 2);
      svg.appendChild(rect);

      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('x', x + barWidth / 2);
      label.setAttribute('y', 185);
      label.setAttribute('fill', 'var(--muted)');
      label.setAttribute('font-size', '9px');
      label.setAttribute('text-anchor', 'middle');
      label.textContent = d.label;
      svg.appendChild(label);

      const val = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      val.setAttribute('x', x + barWidth / 2);
      val.setAttribute('y', y - 5);
      val.setAttribute('fill', 'var(--text)');
      val.setAttribute('font-size', '9px');
      val.setAttribute('text-anchor', 'middle');
      val.textContent = d.value;
      svg.appendChild(val);
    });

    container.innerHTML = '';
    container.appendChild(svg);
  }
};

async function loadCharts() {
  const tab = AppState.activeTab;
  console.log(`Loading charts for tab: ${tab}`);

  if (tab === 'overview') {
    renderOverviewCharts();
  } else if (tab === 'history') {
    renderHistoryCharts();
  } else if (tab === 'budget') {
    renderBudgetCharts();
  } else if (tab === 'why_three') {
    renderWhyThreeCharts();
  }

  // SSE Pipeline Stream fallback
  const pipelineStream = document.getElementById('pipeline-stream');
  if (pipelineStream) {
    pipelineStream.innerHTML = `
      <div class="chart-fallback">
        <div style="font-size: 1.2rem; margin-bottom: 8px;">📡 Readiness: SSE DISCONNECTED</div>
        <div style="font-size: 0.8rem; opacity: 0.8;">The Pipeline Engine Stream requires a persistent EventSource connection to <code>${API_URLS.pipeline_stream}</code>.</div>
        <div style="font-size: 0.75rem; margin-top: 12px; font-family: monospace; color: var(--danger);">[404] Endpoint Not Found - Backend SSE logic is not yet deployed.</div>
      </div>
    `;
  }
}

function renderOverviewCharts() {
  const jobs = UI.getArray(AppState.cachedData.jobs);
  
  // Pipeline Funnel
  const funnelContainer = document.getElementById('pipeline-funnel-chart');
  const funnelData = [
    { label: 'Discovered', value: jobs.length },
    { label: 'Normalized', value: jobs.filter(j => j.status !== 'failed').length },
    { label: 'Accepted', value: jobs.filter(j => j.status === 'accepted').length }
  ];
  ChartUtils.renderFunnel(funnelContainer, funnelData);

  // Industry Distribution
  const industryContainer = document.getElementById('industry-dist-chart');
  const indCounts = {};
  jobs.forEach(j => {
    const ind = j.industry || 'Unknown';
    indCounts[ind] = (indCounts[ind] || 0) + 1;
  });
  const indData = Object.entries(indCounts).map(([label, value]) => ({ label, value }));
  ChartUtils.renderPie(industryContainer, indData);
}

function renderHistoryCharts() {
  const history = UI.getArray(AppState.cachedData.history);
  
  // Accepted Over Time
  const overTimeContainer = document.getElementById('history-over-time-chart');
  const timeData = history.slice(0, 7).reverse().map(b => {
    const ts = b.timestamp ?? b.created_at ?? b.created_at_utc;
    return {
      label: ts ? new Date(ts).toLocaleDateString([], { month: 'short', day: 'numeric' }) : 'Unknown',
      value: b.accepted_count ?? (b.counts ? b.counts.accepted : 0)
    };
  });
  ChartUtils.renderBar(overTimeContainer, timeData);

  // Rejection Distribution
  const rejectionContainer = document.getElementById('rejection-dist-chart');
  const rejCounts = {};
  history.forEach(b => {
    // Assuming history items might have rejection distribution or we aggregate from jobs
    // For now, let's use a placeholder if the data isn't directly in history batch
    if (b.rejections && typeof b.rejections === 'object') {
      Object.entries(b.rejections).forEach(([reason, count]) => {
        rejCounts[reason] = (rejCounts[reason] || 0) + count;
      });
    }
  });
  const rejData = Object.entries(rejCounts).map(([label, value]) => ({ label, value }));
  ChartUtils.renderPie(rejectionContainer, rejData);
}

function renderBudgetCharts() {
  const usage = AppState.cachedData.usage;
  
  // Provider Mix
  const mixContainer = document.getElementById('provider-mix-chart');
  if (usage && usage.providers) {
    const mixData = usage.providers.map(p => ({ label: p.label, value: p.usage_count || 0 }));
    ChartUtils.renderPie(mixContainer, mixData);
  } else {
    ChartUtils.renderFallback(mixContainer);
  }

  // Budget Usage Over Time
  const usageContainer = document.getElementById('budget-usage-chart');
  if (usage && usage.history) {
    const uData = usage.history.map(h => ({
      label: h.date,
      value: h.cost
    }));
    ChartUtils.renderBar(usageContainer, uData);
  } else {
    ChartUtils.renderFallback(usageContainer);
  }
}

function renderWhyThreeCharts() {
  const whyThree = AppState.cachedData.whyThree;
  const container = document.getElementById('resonance-comparison-chart');
  
  if (whyThree && Array.isArray(whyThree.top3)) {
    const compData = whyThree.top3.map(t => ({
      label: t.company || t.title,
      value: Math.round((t.match_score || 0) * 100)
    }));
    ChartUtils.renderBar(container, compData);
  } else {
    ChartUtils.renderFallback(container);
  }
}
