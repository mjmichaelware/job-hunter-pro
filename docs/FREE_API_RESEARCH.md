# Free API Research — 50 sources for opportunity discovery within ~50 mi of 28 E Bryan Ave, 84115

Goal: candidate free/freemium APIs to grow the swarm. Each becomes one
`providers/search/<name>.py` file (discovery) or a `providers/reasoning/*` enricher.
Legend — **D** discovery (job postings), **L** local-data (employers/opportunities to
target), **E** enrichment (reputation/company facts, never discovery). **Key?**: needs a
Secret-Manager key (add via `bash scripts/add_key.sh NAME`) vs keyless. Verify each
endpoint/ToS before wiring; "free tier" limits change.

> Honesty note: a few legacy "job APIs" (Indeed Publisher, GitHub Jobs, Glassdoor public
> API) are deprecated/closed and are intentionally excluded. Items below were grounded in
> June 2026 web research (sources at bottom); confirm exact endpoints at integration time.

## Already integrated (8) — baseline
1. SerpAPI Google Jobs — D, key, budget_class serpapi_quota.
2. SerpAPI Organic — D, key, serpapi_quota (off by default).
3. Adzuna — D, key (APP_ID+APP_KEY), free tier, great US/SLC location filter.
4. USAJobs — D, key+email, federal roles (SLC federal offices).
5. Jooble — D, key, aggregator.
6. Careerjet — D, key (affid), aggregator.
7. The Muse — D, keyless, SLC location param.
8. Google Places/Maps — L+E, key, nearby employers + ratings/reviews.

## Keyless / free job-board APIs to add (D) — fast wins, no secret
9. Arbeitnow Job Board API — keyless JSON, remote+EU heavy (filter for US/remote).
10. Remotive API — keyless, remote roles (`/api/remote-jobs`).
11. RemoteOK API — keyless JSON feed, remote.
12. Jobicy API — keyless, remote, category/geo params.
13. Himalayas API — keyless, remote roles + company data.
14. Working Nomads API — keyless/feed, remote.
15. We Work Remotely — RSS/JSON feeds per category, keyless.
16. Remote.co / Remotewx feeds — keyless RSS where available.
17. Hacker News "Who is hiring" (Algolia HN API) — keyless, monthly hiring threads.
18. Open Skills / Lightcast (legacy) — taxonomy/titles (enrich seeds), keyless data.
19. JobicyremoteRSS / Jobspresso feed — keyless remote feeds.

## Public ATS endpoints (D) — per-company JSON, keyless (target local SLC employers)
> Pattern: pull a known local employer's public board; one provider file can sweep a
> configured list of company slugs near SLC.
20. Greenhouse Boards API — `boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true`, keyless.
21. Lever Postings API — `api.lever.co/v0/postings/{slug}?mode=json`, keyless.
22. Ashby Job Board API — `api.ashbyhq.com/posting-api/job-board/{slug}`, keyless.
23. Recruitee — `{slug}.recruitee.com/api/offers/`, keyless.
24. SmartRecruiters Posting API — `api.smartrecruiters.com/v1/companies/{slug}/postings`, keyless.
25. Workable — `apply.workable.com/api/v1/widget/accounts/{slug}?details=true`, keyless.
26. Personio — `{slug}.jobs.personio.com/xml`, keyless XML.
27. Teamtailor — public career-site JSON (per company), keyless.
28. Rippling/Ashby mirrors & JazzHR feeds — per-company public boards, keyless.

## Government / civic / local-data (L) — who is hiring near 84115
29. Utah DWS jobs.utah.gov (Utah's Online Job Search) — state job DB, SLC filter.
30. Utah Open Data (Socrata SODA API) — keyless/app-token; **Salt Lake City Business
    Licenses** + **~40k Salt Lake County employers** datasets → opportunity targets.
31. Data.SLC.gov (Socrata SODA) — SLC-maintained datasets, keyless/app-token.
32. Salt Lake County Open Data — county business/employer layers.
33. USAspending.gov API — keyless; federal awards → local contractors actively staffing.
34. SAM.gov Entity API — key; registered entities/contractors near SLC.
35. US Census Bureau API — key (free); County Business Patterns = employer counts by
    industry/ZIP (84115 area sizing).
36. Bureau of Labor Statistics (BLS) Public API — key (free); local wage/employment by
    occupation (enriches match + salary context).
37. CareerOneStop Web API (US DOL) — key (free); job search, employers, training near a ZIP.
38. O*NET Web Services — key (free); occupation taxonomy → better role classification.
39. Data.gov CKAN API — keyless; index of additional federal/state datasets.
40. OpenStreetMap Overpass API — keyless; enumerate businesses (amenity/shop/office)
    within a radius of 40.71,-111.89 → broad 50-mi opportunity radar with zero job-post
    dependency.
41. Nominatim (OSM geocoding) — keyless; address/zip → lat/lng fallback for origin override.
42. US ZIP / Zippopotam.us — keyless; ZIP→coords for the radius-center input.

## Places / business directories (L+E)
43. Yelp Fusion API — key (free tier); local businesses + ratings/reviews near SLC.
44. Foursquare Places API — key (free tier); place search + categories within radius.
45. Google Places Nearby/Text (already keyed) — expand category sweeps per industry.
46. Wikidata / Wikipedia API — keyless; company facts (size, HQ) for enrichment.
47. OpenCorporates API — key (free tier); legal-entity/company registry data.

## Enrichment / reputation (E) — reasoning support, NEVER discovery
48. Hunter.io API — key (free tier); find a hiring-contact email at a resolved company.
49. Clearbit / Abstract Company Enrichment (free tier) — company size/industry signals.
50. BBB / public review aggregation via SerpAPI Organic (budget-gated) — feeds the future
    "Core Rating" (Google + Glassdoor-mention + BBB), reasoning-only, evidence-cited.

## Notes for the swarm build
- Highest-yield, no-secret first: #9–#28 (keyless boards + ATS) and #29–#42 (civic/OSM) —
  these prove the 50-source fanout without spending a cent.
- Radius/origin: #40–#42 directly enable the user-set 50-mi center (84115) feature.
- "Core Rating": #43, #46, #47, #50 are the honest inputs to replace bare Google stars.
- Each is one `providers/search/<name>.py` (copy `_template.py`); secrets only via
  `scripts/add_key.sh` + `--set-secrets` (see `docs/SWARM_PROVIDERS.md`).

## Sources
- https://brightdata.com/blog/web-data/best-job-apis
- https://jobapis.github.io/
- https://www.arbeitnow.com/blog/job-board-api
- https://publicapis.io/category/jobs
- https://fantastic.jobs/article/ats-with-api
- https://cavuno.com/blog/ats-platforms-public-job-posting-apis
- https://opendata.utah.gov/Permit-and-Licensing/Salt-Lake-City-Business-Licenses/hi6r-u5gn/data
- https://data.slc.gov/
- https://opendata.utah.gov/salt-lake-county
- https://jobs.utah.gov/
