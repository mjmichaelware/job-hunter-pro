const escapeHTML=value=>String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[char]));

const UI={
  renderJobsInto(targetId,jobs=[]){
    const grid=document.getElementById(targetId)||document.querySelector(".grid-system,#jobs");
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

      const ri=job.review_intelligence||{};
      const rating=job.google_rating||ri.google_rating;
      const reviewCount=job.google_review_count||ri.google_review_count;
      const reviewScore=job.review_score||ri.review_score;
      const consistency=job.consistency_score||ri.consistency_score;
      const risk=job.risk_level||ri.risk_level||"unknown";
      const chefs=Array.isArray(job.chef_names)&&job.chef_names.length?`Chef/public names: ${job.chef_names.map(escapeHTML).join(", ")}`:"No chef names found yet";

      return `<article class="job-card reveal" style="animation-delay:${index*35}ms">
        <span class="match">${escapeHTML(match)}</span>
        <h3>${title}</h3>
        <div class="company">${company}</div>
        <p class="meta">${address} • ${commute} • ${radius}</p>
        <p class="meta">${rating?escapeHTML(rating)+"★":"No rating"} • ${reviewCount?escapeHTML(reviewCount)+" reviews":"review count unknown"} • Review score ${reviewScore??"unscored"} • Consistency ${consistency??"—"} • Risk: ${escapeHTML(risk)}</p>
        <div class="salary">${salary}</div>
        <div class="tag-row">${tags.map(t=>`<span class="tag">${escapeHTML(t)}</span>`).join("")}<span class="tag">${escapeHTML(job.role_family||"food-service")}</span><span class="tag">AI: ${ai}</span></div>
        <p class="description">${description}</p>
        <p class="description">${chefs}</p>
        <div class="cluster">
          <button class="action-btn" data-action="toggle-details">View Details</button>
          ${url?`<a class="btn btn-ghost" href="${url}" target="_blank" rel="noopener noreferrer">Apply</a>`:""}
          ${job.place_id?`<a class="btn btn-ghost" href="/api/research/place?place_id=${escapeHTML(job.place_id)}&name=${encodeURIComponent(company)}" target="_blank">Research</a>`:""}
        </div>
      </article>`;
    }).join("");

    UI.observeReveals();
  },

  renderJobs(jobs=[]){
    return UI.renderJobsInto("jobGrid",jobs);
  },

  observeReveals(){
    const items=document.querySelectorAll(".reveal:not(.visible)");
    if(!("IntersectionObserver"in window)){
      items.forEach(el=>el.classList.add("visible"));
      return;
    }
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
    UI.observeReveals();
  }
};

document.addEventListener("DOMContentLoaded",()=>UI.bind());
window.UI=UI;
