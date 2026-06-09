---
name: jhp-git-commit-push
description: Stage, commit, and push only after proof and explicit approval.
allowed-tools: Bash(git status *) Bash(git diff *) Bash(rg *) Bash(python3 -m py_compile *) Bash(bash .claude/scripts/safe_local_proof.sh)
---

# jhp-git-commit-push

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
