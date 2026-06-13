const escapeHTML=value=>String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[char]));

function val(id){ return document.getElementById(id)?.value || ""; }

function params(){
  const p = new URLSearchParams();
  for (const id of ["min_rating","max_radius","max_transit","min_score","role","house","q"]) {
    const v = val(id);
    if (v && v !== "all") p.set(id, v);
  }
  return p.toString();
}

function setStatus(t){
  const el=document.getElementById("status");
  if(el) el.textContent=t;
}

function updateStats(p){
  if("count" in p && document.getElementById("statJobs")) document.getElementById("statJobs").textContent=p.count;
  if("raw_count" in p && document.getElementById("statRaw")) document.getElementById("statRaw").textContent=p.raw_count;
  if("nearby_restaurant_count" in p && document.getElementById("statOpps")) document.getElementById("statOpps").textContent=p.nearby_restaurant_count;
}

const UI={
  renderJobsInto(targetId,jobs=[]){
    const grid=document.getElementById(targetId)||document.querySelector(".grid-system");
    if(!grid)return;
    if(!Array.isArray(jobs)||jobs.length===0){
      grid.innerHTML=`<div class="empty-state"><h3>No jobs in this view</h3><p>Try loading live jobs, changing filters, or using opportunities/history.</p></div>`;
      return;
    }
    grid.innerHTML=jobs.map((job,index)=>{
      const title=escapeHTML(job.title||"Untitled Role");
      const company=escapeHTML(job.restaurant_name||job.resolved_place_name||job.company||"Restaurant not listed");
      const address=escapeHTML(job.resolved_address||job.location||"Location not listed");
      const salary=escapeHTML(job.salary||"Salary not listed");
      const description=escapeHTML(job.description||"No description available.");
      const commute=escapeHTML(job.commute_label||"Transit unavailable");
      const radius=escapeHTML(job.radius_label||"Radius unavailable");
      const ai=escapeHTML(job.ai_provider||"resolver");
      const url=escapeHTML(job.source_url||"");
      const tags=Array.isArray(job.tags)?job.tags.slice(0,6):[];
      const match=Number.isFinite(Number(job.match))?`${Math.round(Number(job.match))}% match`:"Live";
      const rating=job.google_rating||job.review_intelligence?.google_rating;
      const reviewCount=job.google_review_count||job.review_intelligence?.google_review_count;
      const reviewScore=job.review_score||job.review_intelligence?.review_score;
      const consistency=job.consistency_score||job.review_intelligence?.consistency_score;
      const risk=job.risk_level||job.review_intelligence?.risk_level||"unknown";
      return `<article class="job-card reveal" style="animation-delay:${index*35}ms">
        <span class="match">${escapeHTML(match)}</span>
        <h3>${title}</h3>
        <div class="company">${company}</div>
        <p class="meta">${address} • ${commute} • ${radius}</p>
        <p class="meta">${rating?escapeHTML(rating)+"★":"No rating"} • ${reviewCount?escapeHTML(reviewCount)+" reviews":"review count unknown"} • Review score ${reviewScore??"unscored"} • Consistency ${consistency??"—"} • Risk: ${escapeHTML(risk)}</p>
        <div class="salary">${salary}</div>
        <div class="tag-row">${tags.map(t=>`<span class="tag">${escapeHTML(t)}</span>`).join("")}<span class="tag">${escapeHTML(job.role_family||"food-service")}</span><span class="tag">AI: ${ai}</span></div>
        <p class="description">${description}</p>
        <div class="cluster">
          <button class="action-btn" data-action="toggle-details">View Details</button>
          ${url?`<a class="btn btn-ghost" href="${url}" target="_blank" rel="noopener noreferrer">Apply</a>`:""}
          ${job.place_id?`<a class="btn btn-ghost" href="/api/research/place?place_id=${escapeHTML(job.place_id)}&name=${encodeURIComponent(company)}" target="_blank">Research</a>`:""}
        </div>
      </article>`;
    }).join("");
    UI.observeReveals();
  },
  renderJobs(jobs=[]){ UI.renderJobsInto("jobGrid",jobs); },
  observeReveals(){
    const items=document.querySelectorAll(".reveal:not(.visible)");
    if(!("IntersectionObserver"in window)){items.forEach(el=>el.classList.add("visible"));return;}
    const observer=new IntersectionObserver(entries=>{
      entries.forEach(entry=>{
        if(entry.isIntersecting){
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },{threshold:.12});
    items.forEach(el=>observer.observe(el));
  },
  bind(){
    document.addEventListener("click",event=>{
      const btn=event.target.closest("[data-action='toggle-details']");
      if(!btn)return;
      const card=btn.closest(".job-card");
      card.classList.toggle("expanded");
      btn.textContent=card.classList.contains("expanded")?"Hide Details":"View Details";
    });
  }
};

function loadUsage(){
  fetch("/api/usage").then(r=>r.json()).then(p=>{
    const left=p?.serpapi?.total_searches_left??"—";
    const el=document.getElementById("statSerp");
    if(el) el.textContent=left;
  }).catch(()=>{});
}

function loadLiveJobs(){
  const qs=params();
  setStatus("Running budget-limited live discovery. This may spend SerpAPI searches.");
  fetch("/api/jobs"+(qs?"?"+qs:""))
    .then(r=>r.json())
    .then(p=>{updateStats(p);setStatus(`Live jobs loaded: ${p.count||0}. Raw scanned: ${p.raw_count||0}.`);UI.renderJobsInto("jobGrid",p.data||[]);})
    .catch(e=>setStatus("Live job load failed: "+e));
}

function loadOpportunities(){
  const qs=params();
  setStatus("Loading Google Places opportunities without SerpAPI.");
  fetch("/api/opportunities"+(qs?"?"+qs:""))
    .then(r=>r.json())
    .then(p=>{
      const opp=document.getElementById("statOpps"); if(opp) opp.textContent=p.count||0;
      setStatus(`Loaded ${p.count||0} nearby restaurant opportunities.`);
      const rows=(p.data||[]).map(x=>`<tr>
        <td>${escapeHTML(x.name||"")}</td>
        <td>${escapeHTML(x.google_rating||"—")}</td>
        <td>${escapeHTML(x.google_review_count||"—")}</td>
        <td>${escapeHTML(x.radius_label||"—")}</td>
        <td>${escapeHTML(x.business_status||"—")}</td>
        <td>${x.place_id?`<a href="/api/research/place?place_id=${escapeHTML(x.place_id)}&name=${encodeURIComponent(x.name||"")}" target="_blank">Research</a>`:""}</td>
      </tr>`).join("");
      const body=document.getElementById("opportunityRows");
      if(body) body.innerHTML=rows||"<tr><td colspan='6'>No opportunities loaded.</td></tr>";
    })
    .catch(e=>setStatus("Opportunities failed: "+e));
}

function loadHistory(){
  const qs=params();
  setStatus("Loading stored batch history.");
  fetch("/api/history?hours=24"+(qs?"&"+qs:""))
    .then(r=>r.json())
    .then(p=>{
      const jobs=document.getElementById("statJobs"); if(jobs) jobs.textContent=p.job_count||0;
      setStatus(`History loaded: ${p.job_count||0} jobs across ${p.batch_count||0} batches.`);
      UI.renderJobsInto("jobGrid",p.data||[]);
      const rows=(p.batches||[]).map(b=>`<tr>
        <td>${escapeHTML(b.object_name||"")}</td>
        <td>${escapeHTML(b.created_at_utc||"")}</td>
        <td>${escapeHTML(b.counts?.accepted??"—")}</td>
        <td>${escapeHTML(b.counts?.rejected??"—")}</td>
        <td>${escapeHTML(b.counts?.raw??"—")}</td>
      </tr>`).join("");
      const body=document.getElementById("historyRows");
      if(body) body.innerHTML=rows||"<tr><td colspan='5'>No batches stored yet.</td></tr>";
    })
    .catch(e=>setStatus("History failed: "+e));
}

function loadProviderStatus() {
  setStatus("Loading provider status...");
  fetch("/api/providers/status")
    .then(res => res.json())
    .then(data => {
      const providers = data.providers || [];
      const oppsProvider = providers.find(p => p.supports_opportunities && p.status === 'available');
      const jobsProvider = providers.find(p => p.supports_live_jobs && p.status === 'available');

      if (!oppsProvider) {
        document.querySelector("[onclick='loadOpportunities()']").disabled = true;
        setStatus("Opportunity provider is disabled, possibly for cost control.");
      }
      if (!jobsProvider) {
          document.querySelector("[onclick='loadLiveJobs()']").disabled = true;
          setStatus("Live job discovery providers are disabled.");
      }
    })
    .catch(e => setStatus("Provider status check failed: " + e));
}

document.addEventListener("DOMContentLoaded",()=>{
  UI.bind();
  loadProviderStatus();
  loadUsage();
  loadOpportunities();
  loadHistory();
});
window.UI=UI;
