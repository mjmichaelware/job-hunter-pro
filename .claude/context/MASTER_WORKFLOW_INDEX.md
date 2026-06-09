# Master Workflow Index — Job Hunter Pro

This is the top-level workflow map. Future AI agents must read this before patching.

## Read order

1. .claude/context/DEFCON1_AGENT_RULES.md
2. .claude/context/HANDOFF_WORKFLOW.md
3. .claude/context/AI_AGENT_TAKEOVER_PACKET.md
4. .claude/context/SESSION_STATE.md
5. .claude/context/DOCUMENT_CONTRADICTION_MATRIX.md
6. .claude/context/CANONICAL_RESOLVED_SPEC.md
7. .claude/context/CURRENT_CODE_MAP.md
8. .claude/context/STUB_PLACEHOLDER_AUDIT.md
9. .claude/context/BUG_LEDGER.md
10. .claude/context/FINAL_PATCH_PLAN.md
11. .claude/context/UI_BACKEND_PARITY_WORKFLOW.md
12. .claude/tasks/UI_BACKEND_PARITY_AGENT_PROMPT.md

## Workflow layers

- Document reconciliation workflow: resolve contradictions before treating docs as truth.
- Canonical spec workflow: compare code against CANONICAL_RESOLVED_SPEC.md, not raw docs.
- Stub and placeholder audit workflow: find fake, dead, placeholder, and disconnected code.
- Patch-plan workflow: write plan before app-logic edits.
- UI/backend parity workflow: every backend capability must render truthfully in the UI, and every UI control must map to a real endpoint or be labeled pending.
- Handoff workflow: update state, proof, commit, push when authorized, export tar.gz.
- Deploy workflow: do not deploy until S12 and explicit deploy authorization.

## Product intent

Job Hunter Pro should become a persistent, decoupled, provider-aware intelligence dashboard where adding a provider, changing a button, changing UI styling, or adding an API is modular instead of a rewrite.

The UI should truthfully show accepted, unresolved, and rejected jobs; provider breakdown; apply/source URLs; usage/budget; history; opportunities; proof telemetry; and beautiful mobile-first cards.

The reference capability is seeing many relevant jobs around a configurable origin such as 84115 within radii like 2 or 5 miles, without hardcoding that example as the only target.

## Absolute rules

- No secrets printed or hardcoded.
- No live /api/jobs on page load.
- No /api/ingest unless explicitly authorized.
- No deploy unless explicitly authorized.
- No Scheduler token in URL.
- LLM APIs enrich/classify only. They do not discover jobs.
- Discovery providers are SerpAPI Jobs, SerpAPI Organic, Adzuna, USAJobs, Jooble, Careerjet, The Muse, and Google Places/opportunities.
- Inspect, compile, safe proof, then commit/deploy decisions.
- Android ARM64 Termux plus Ubuntu proot is the development environment.
- Do not use heredocs in user-facing terminal commands.
