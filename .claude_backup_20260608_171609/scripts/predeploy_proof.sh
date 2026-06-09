#!/usr/bin/env bash
set -euo pipefail
bash .claude/scripts/inspect_stack.sh
bash .claude/scripts/safe_local_proof.sh
echo "PASS predeploy local proof. Deploy only after explicit approval."
