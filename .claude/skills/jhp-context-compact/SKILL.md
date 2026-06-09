---
name: jhp-context-compact
description: Compact durable state at 75 percent context without rereading everything.
allowed-tools: Bash(git status *) Bash(git diff *) Bash(rg *) Bash(python3 -m py_compile *) Bash(bash .claude/scripts/safe_local_proof.sh)
---

# jhp-context-compact

Use project rules from .claude/CLAUDE.md.

Never print secrets.
Never call /api/ingest unless explicitly instructed.
Never call live /api/jobs unless explicitly instructed.
Never deploy unless explicitly instructed.

For live jobs:
- Missing address/radius/transit becomes resolution_flags, not deletion.
- All available search providers get fair fanout.
- LLMs are enrichment/classification only.
- UI shows accepted plus unresolved candidates.
- Provider breakdown and source URLs are preserved.
