const escapeHTML=value=>String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[char]));

const UI={
  renderJobs(jobs=[]){
    const grid=document.querySelector(".grid-system,#jobs");
    if(!grid)return;

    if(!Array.isArray(jobs)||jobs.length===0){
      grid.innerHTML=`<div class="empty-state"><h3>No matching restaurant jobs found yet</h3><p>The live API is working, but no food-service jobs passed the 2.5 mile + under 35 minute transit filter right now. Try Refresh again later.</p></div>`;
      return;
    }

    grid.innerHTML=jobs.map((job,index)=>{
      const title=escapeHTML(job.title||"Untitled Role");
      const company=escapeHTML(job.company||"Company not listed");
      const location=escapeHTML(job.location||"Location not listed");
      const salary=escapeHTML(job.salary||"Salary not listed");
      const description=escapeHTML(job.description||"No description available yet.");
      const commute=escapeHTML(job.commute_label||"Commute unavailable");
      const distance=escapeHTML(job.distance_label||"Distance unavailable");
      const tags=Array.isArray(job.tags)?job.tags.slice(0,5):[];
      const match=Number.isFinite(Number(job.match))?`${Math.round(Number(job.match))}% match`:"Live";
      const url=escapeHTML(job.source_url||"");

      return `
        <article class="job-card reveal" style="animation-delay:${index*45}ms">
          <span class="match">${escapeHTML(match)}</span>
          <h3>${title}</h3>
          <div class="company">${company}</div>
          <p class="meta">${location} • ${commute} • ${distance}</p>
          <div class="salary">${salary}</div>
          <div class="tag-row">${tags.map(tag=>`<span class="tag">${escapeHTML(tag)}</span>`).join("")}</div>
          <p class="description">${description}</p>
          <div class="cluster">
            <button class="action-btn" data-action="toggle-details">View Details</button>
            ${url?`<a class="btn btn-ghost" href="${url}" target="_blank" rel="noopener noreferrer">Apply</a>`:""}
          </div>
        </article>`;
    }).join("");

    UI.observeReveals();
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

document.addEventListener("DOMContentLoaded",()=>{
  UI.bind();
  console.log("Job Hunter Pro Live Restaurant UI Initialized");
});

window.UI=UI;
