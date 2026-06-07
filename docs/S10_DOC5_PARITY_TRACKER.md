# S10 Document 5 Parity Tracker

Status: S10-A safe shell committed.
This file prevents overclaiming. Document 5 is not fully implemented yet.

## S10-A — Done / committed
- 8-tab web shell exists.
- Premium dark cockpit baseline exists.
- Safe boot guard exists.
- No frontend /api/ingest.
- No generic API_URLS.jobs.
- No direct live /api/jobs fetch.
- No configured fake/demo frontend terms.
- Known unsafe debug scripts disabled.
- Changed Python files compile.

## S10-B & S10-C — Done / committed
- API Contract Reality Pass (S10-B) complete. `S10_API_CONTRACT_MATRIX.md` generated.
- Core Renderer Truth Upgrade (S10-C) complete. All renderers hardened to prevent crashes on placeholder data, utilizing honest empty/unavailable states.
- No fake data arrays utilized.

## S10-D — Core UI parity still required
- Advanced filter drawer:
  - search mode
  - radius/location
  - industry
  - provider
  - status
  - sort
  - min match score
  - max walk minutes
  - max transit minutes
  - min rating
  - min review score
  - job type
  - pay hint
  - remote/onsite
  - provider include/exclude
  - batch
  - time range
  - rejection reason
  - classification confidence
  - place status
  - application state
  - duplicate state
- Evidence drawer with all required fields:
  - raw_title
  - normalized_title
  - company
  - source
  - provider_id
  - industry_scores
  - accepted/rejected status
  - rejection_reasons
  - dedupe_key
  - place_resolution
  - review_score
  - match_score
  - budget_cost
  - query_seed
  - discovery_mode
  - timestamp
- Provider UI:
  - discovery providers separated from reasoning providers
  - configured/missing key state
  - dormant/live/budget guarded state
  - last used
  - allowed actions
- Budget reactor:
  - real usage
  - dry-run ghost burn
  - live cost warning
  - blocked over-budget state
  - historical/cached fallback state
- Charts:
  - funnel
  - provider mix
  - budget usage
  - accepted over time
  - rejection distribution
  - industry distribution
  - opportunity categories
  - review rating distribution
  - no-data chart states

## S10-C — Advanced visual systems still required
- View Transitions API shared-element card-to-evidence morph.
- Web Animations API spring/physics motion.
- Scroll-driven CSS animations.
- Container queries / subgrid / anchor-positioning bento layout.
- OKLCH industry theming.
- Variable-font confidence rendering.
- Houdini/continuous-corner visual treatment or fallback.
- WebGL2/WebGPU ambient telemetry canvas, feature-detected.
- prefers-reduced-motion support.
- Save-Data / low-power fallback.

## S10-D — Runtime/data systems still required
- Server-Sent Events pipeline stream.
- Live pipeline reactor:
  discover -> normalize -> resolve_place -> classify -> score -> filter -> dedupe -> store.
- Rejection shedding UI:
  - not_food_service
  - outside_radius
  - ambiguous_place_resolution
  - duplicate
- IndexedDB cached history.
- PWA shell / manifest / service worker.
- ARIA live region for pipeline counts.
- Chart table fallbacks.
- Keyboard navigation and command palette.
- Bilingual display where source supports it.
- Markov vacancy prediction radar as beta and never mixed with confirmed jobs.
- WebGPU/WASM local inference preview as optional future tier only.

## S10-E — Backend/API gaps to verify before claiming parity
- /api/providers live availability.
- /api/industries live availability.
- /api/why-three availability.
- Evidence payload fields availability.
- Budget usage payload shape.
- Dry-run query plan payload shape.
- Application status payload shape.
- SSE endpoint existence.
- Cached history/batch shape.
- Review score component shape.
- Place resolution notes shape.

## Deployment rule
Do not deploy until S12.
Do not claim Document 5 is fully implemented until this tracker is closed.
