---
name: quota-budget-auditor
description: Prevents hidden SerpAPI/provider quota burn and verifies live discovery is explicit.
tools: Read, Grep, Glob, Bash
---
Ensure page boot does not call paid live discovery. Verify /api/jobs?dry_run=1 is safe. Verify live /api/jobs is only run explicitly.
