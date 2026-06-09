# DEFCON 1 Agent Rules — Job Hunter Pro

This file exists to prevent context loss, quota waste, unsafe patches, and terminal-breaking paste patterns.

## Terminal safety

- Do not use heredocs in user-facing commands.
- Do not use cat <<EOF in user-facing commands.
- Do not paste huge quoted blocks into Termux.
- Prefer checked-in scripts, small printf writers, or existing files.
- Remember the environment is Android ARM64 Termux plus Ubuntu proot.

## Token and context safety

- Do not re-read all documents unless required.
- Start from SESSION_STATE.md and AI_AGENT_TAKEOVER_PACKET.md.
- Use the audit packet to resume instead of repeating the full audit.
- If context reaches roughly 75 percent, update SESSION_STATE.md and export a fresh handoff packet.

## Absolute project safety

- Do not print secrets.
- Do not hardcode secrets.
- Do not call live /api/jobs unless explicitly authorized.
- Do not call /api/ingest unless explicitly authorized.
- Do not deploy unless explicitly authorized.
- Do not push unless explicitly authorized.
- LLM APIs are enrichment and classification only, never job discovery.
- Job discovery sources are SerpAPI Jobs, SerpAPI Organic, Adzuna, USAJobs, Jooble, Careerjet, The Muse, and Google Places or opportunities.

## Patch safety

- Inspect current code before patching.
- Confirm the defect still exists.
- Patch surgically.
- Run python compile.
- Run safe local proof.
- Run git diff check.
- Stop before deploy.
