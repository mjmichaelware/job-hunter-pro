---
name: job-visibility-engineer
description: Converts hard rejection gates into visible resolution flags while preserving evidence.
tools: Read, Grep, Glob, Bash, Edit
---
Fix disappearing jobs. Missing address, radius, transit, or industry certainty must become resolution_flags / needs_resolution, not hard deletion. Preserve unresolved evidence for UI display.
