# App Mission — Job Hunter Pro / Job AI Hunting

Target app: Job Hunter Pro.
Owner: Michael Ware.

Mission: build and repair a persistent AI-assisted job-hunting intelligence dashboard.

The app must truthfully connect backend provider discovery, enrichment/classification, scoring, persistence, usage/budget, history, opportunities, and frontend rendering.

Reference capability: show many relevant jobs around a configurable origin such as 84115 within configurable radii such as 2 miles or 5 miles, without hardcoding that example as the only target.

The workflow must enforce UI/backend parity: every backend capability must render beautifully and truthfully in the UI, and every UI control must map to a real endpoint or be clearly labeled pending.

Discovery providers: SerpAPI Jobs, SerpAPI Organic, Adzuna, USAJobs, Jooble, Careerjet, The Muse, and Google Places/opportunities.

LLM APIs are enrichment/classification only. They do not discover jobs.

Current known priority defects from audit:
- CRIT-1: api/index.py rejection_reasons() builds reasons but returns [].
- CRIT-2: /api/ingest OIDC verification is only a Bearer-prefix check.
- HIGH-3: reasoning providers return fake enrichment strings when keys are present.
- HIGH-4: live /api/jobs is restaurant-only despite the multi-industry registry.
- HIGH-5: review-score formula does not match canonical resolved spec.

Do not deploy.
Do not call live /api/jobs.
Do not call /api/ingest.
Do not print secrets.
Do not patch blindly.
